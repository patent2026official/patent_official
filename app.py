"""
딸깍봇 — Slack에서 @딸깍봇 멘션으로 Claude AI에게 업무를 지시하는 봇
"""

import re
import logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic

import config
from tools import ALL_TOOLS, handle_tool_call

# ── 로깅 ────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("딸깍봇")

# ── 앱 초기화 ───────────────────────────────────────────────────
app = App(token=config.SLACK_BOT_TOKEN)
claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


# ── 멘션 핸들러 ─────────────────────────────────────────────────
@app.event("app_mention")
def handle_mention(event, say, client):
    """@딸깍봇 멘션이 오면 Claude에게 전달하고 결과를 Slack에 응답"""
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])
    raw_text = event.get("text", "")

    # 봇 멘션 태그 제거 → 순수 사용자 메시지
    user_msg = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()
    if not user_msg:
        say(text="무엇을 도와드릴까요? 작업 내용을 알려주세요.", thread_ts=thread_ts)
        return

    # 사용자 정보 조회
    user_info = client.users_info(user=event["user"])
    user_name = user_info["user"]["real_name"] if user_info["ok"] else "팀원"

    # 처리 중 리액션
    try:
        client.reactions_add(channel=channel, timestamp=event["ts"], name="hourglass_flowing_sand")
    except Exception:
        pass

    logger.info(f"[{user_name}] {user_msg}")

    # ── Claude API 호출 (tool_use 루프) ──────────────────────
    messages = [{"role": "user", "content": f"[{user_name}이(가) Slack에서 요청]\n{user_msg}"}]

    try:
        response_text = _run_claude(messages)
    except Exception as e:
        logger.error(f"Claude 호출 실패: {e}")
        response_text = f":x: 처리 중 오류가 발생했습니다.\n```{e}```"

    # 리액션 교체
    try:
        client.reactions_remove(channel=channel, timestamp=event["ts"], name="hourglass_flowing_sand")
        client.reactions_add(channel=channel, timestamp=event["ts"], name="white_check_mark")
    except Exception:
        pass

    # 응답 (4000자 초과 시 분할)
    _send_long_message(say, response_text, thread_ts)


# ── Claude 실행 (tool_use 루프) ─────────────────────────────────
def _run_claude(messages: list, max_turns: int = 10) -> str:
    """Claude API를 호출하고, tool_use가 있으면 자동으로 도구 실행 후 재호출"""

    for _ in range(max_turns):
        resp = claude.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=4096,
            system=config.SYSTEM_PROMPT,
            tools=ALL_TOOLS,
            messages=messages,
        )

        # stop_reason == "end_turn" → 최종 응답
        if resp.stop_reason == "end_turn":
            return _extract_text(resp)

        # stop_reason == "tool_use" → 도구 실행
        if resp.stop_reason == "tool_use":
            # assistant 메시지 추가
            messages.append({"role": "assistant", "content": resp.content})

            # 도구 실행 결과 수집
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    logger.info(f"  도구 호출: {block.name}({block.input})")
                    result = handle_tool_call(block.name, block.input)
                    logger.info(f"  도구 결과: {result[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # 기타 stop_reason
        return _extract_text(resp)

    return ":warning: 최대 도구 호출 횟수를 초과했습니다."


def _extract_text(resp) -> str:
    """Claude 응답에서 text 블록만 추출"""
    texts = []
    for block in resp.content:
        if hasattr(block, "text"):
            texts.append(block.text)
    return "\n".join(texts) or "(응답 없음)"


# ── Slack 메시지 분할 전송 ──────────────────────────────────────
def _send_long_message(say, text: str, thread_ts: str, limit: int = 3900):
    """Slack 메시지 길이 제한(4000자)에 맞게 분할 전송"""
    if len(text) <= limit:
        say(text=text, thread_ts=thread_ts)
        return

    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        # 줄바꿈 기준으로 자르기
        idx = text.rfind("\n", 0, limit)
        if idx == -1:
            idx = limit
        chunks.append(text[:idx])
        text = text[idx:].lstrip("\n")

    for i, chunk in enumerate(chunks):
        prefix = f"({i+1}/{len(chunks)})\n" if len(chunks) > 1 else ""
        say(text=prefix + chunk, thread_ts=thread_ts)


# ── DM 핸들러 (선택) ───────────────────────────────────────────
@app.event("message")
def handle_dm(event, say, client):
    """DM으로 온 메시지도 처리 (봇에게 직접 DM)"""
    # 봇 자신의 메시지, 서브타입 메시지 무시
    if event.get("bot_id") or event.get("subtype"):
        return
    # 채널 타입이 im(DM)인 경우만
    channel_type = event.get("channel_type", "")
    if channel_type != "im":
        return

    user_msg = event.get("text", "").strip()
    if not user_msg:
        return

    thread_ts = event.get("thread_ts", event["ts"])
    user_info = client.users_info(user=event["user"])
    user_name = user_info["user"]["real_name"] if user_info["ok"] else "팀원"

    messages = [{"role": "user", "content": f"[{user_name}이(가) DM으로 요청]\n{user_msg}"}]

    try:
        response_text = _run_claude(messages)
    except Exception as e:
        response_text = f":x: 오류: {e}"

    _send_long_message(say, response_text, thread_ts)


# ── 실행 ────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"🤖 {config.BOT_NAME} 시작!")
    handler = SocketModeHandler(app, config.SLACK_APP_TOKEN)
    handler.start()
