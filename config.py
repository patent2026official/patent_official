import os
from dotenv import load_dotenv
load_dotenv()
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_APP_TOKEN = os.getenv('SLACK_APP_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CLAUDE_MODEL = os.getenv('CLAUDE_MODEL', 'claude-sonnet-4-20250514')
JIRA_BASE_URL = os.getenv('JIRA_BASE_URL', 'https://aeconsultingofficial.atlassian.net')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY', 'SCRUM')
NOTION_API_KEY = os.getenv('NOTION_API_KEY')
NOTION_TASKS_DB_ID = os.getenv('NOTION_TASKS_DB_ID', '32c51ceb4ac880dd84eef8e9462ab03e')
BOT_NAME = os.getenv('BOT_NAME', '\ub538\uae4d\ubd07')
NOTIFY_CHANNEL_ID = os.getenv('NOTIFY_CHANNEL_ID', 'C0ARDGL6ZMM')
SYSTEM_PROMPT = f"당신은 '{BOT_NAME}'입니다. AE 컨설팅 팀의 AI 업무 어시스턴트입니다.\n항상 한국어로 응답하세요. 간결하고 핵심만 전달하세요.\nJira 이슈 생성/수정/조회, Notion 문서 생성/수정/조회가 가능합니다.\n응답은 Slack 마크다운 형식으로 작성하세요."
