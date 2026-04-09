import os
from dotenv import load_dotenv

load_dotenv()

# Slack
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

# Jira
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://aeconsultingofficial.atlassian.net")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "SCRUM")

# Notion
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_MAIN_PAGE_ID = os.getenv("NOTION_MAIN_PAGE_ID")
NOTION_TASKS_DB_ID = os.getenv("NOTION_TASKS_DB_ID")

# Bot
BOT_NAME = os.getenv("BOT_NAME", "딸깍봇")
NOTIFY_CHANNEL_ID = os.getenv("NOTIFY_CHANNEL_ID", "C0ARDGL6ZMM")

SYSTEM_PROMPT = f"""당신은 '{BOT_NAME}'입니다. AE 컨설팅 팀의 AI 업무 어시스턴트입니다.
항상 한국어로 응답하세요. 간결하고 핵심만 전달하세요.

당신이 할 수 있는 것:
1. Jira 이슈 생성/수정/조회/상태변경
2. Notion 문서 생성/수정/조회
3. 일반 질문 답변, 코드 작성, 문서 초안 작성

규칙:
- 응답은 Slack 마크다운 형식으로 작성
- 작업 완료 시 결과를 간단히 요약
- 에러 발생 시 원인과 해결 방법 제시
- 민감 정보(API 키 등)는 절대 노출 금지
"""
