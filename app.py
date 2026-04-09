import re, logging
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import anthropic, config
from tools import ALL_TOOLS, handle_tool_call

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('ddalgak')
app = App(token=config.SLACK_BOT_TOKEN)
claude = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

@app.event('app_mention')
def handle_mention(event, say, client):
    channel = event['channel']
    thread_ts = event.get('thread_ts', event['ts'])
    user_msg = re.sub(r'<@[A-Z0-9]+>', '', event.get('text','')).strip()
    if not user_msg:
        say(text='무엇을 도와드릴까요?', thread_ts=thread_ts); return
    try:
        client.reactions_add(channel=channel, timestamp=event['ts'], name='hourglass_flowing_sand')
    except: pass
    user_info = client.users_info(user=event['user'])
    user_name = user_info['user']['real_name'] if user_info['ok'] else '팀원'
    messages = [{'role':'user','content':f'[{user_name}] {user_msg}'}]
    try:
        text = run_claude(messages)
    except Exception as e:
        text = f':x: 오류: {e}'
    try:
        client.reactions_remove(channel=channel, timestamp=event['ts'], name='hourglass_flowing_sand')
        client.reactions_add(channel=channel, timestamp=event['ts'], name='white_check_mark')
    except: pass
    for i in range(0, len(text), 3900):
        say(text=text[i:i+3900], thread_ts=thread_ts)

@app.event('message')
def handle_dm(event, say, client):
    if event.get('bot_id') or event.get('subtype') or event.get('channel_type') != 'im': return
    user_msg = event.get('text','').strip()
    if not user_msg: return
    messages = [{'role':'user','content':user_msg}]
    try: text = run_claude(messages)
    except Exception as e: text = f':x: 오류: {e}'
    say(text=text, thread_ts=event.get('thread_ts', event['ts']))

def run_claude(messages, max_turns=10):
    for _ in range(max_turns):
        resp = claude.messages.create(model=config.CLAUDE_MODEL, max_tokens=4096, system=config.SYSTEM_PROMPT, tools=ALL_TOOLS, messages=messages)
        if resp.stop_reason == 'end_turn':
            return '\n'.join(b.text for b in resp.content if hasattr(b,'text')) or '(응답 없음)'
        if resp.stop_reason == 'tool_use':
            messages.append({'role':'assistant','content':resp.content})
            results = []
            for b in resp.content:
                if b.type == 'tool_use':
                    r = handle_tool_call(b.name, b.input)
                    results.append({'type':'tool_result','tool_use_id':b.id,'content':r})
            messages.append({'role':'user','content':results})
            continue
        return '\n'.join(b.text for b in resp.content if hasattr(b,'text')) or '(응답 없음)'
    return '최대 호출 횟수 초과'

if __name__ == '__main__':
    logger.info(f'{config.BOT_NAME} 시작!')
    SocketModeHandler(app, config.SLACK_APP_TOKEN).start()
