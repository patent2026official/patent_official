# 딸깍봇 설치 가이드

## 1단계: Slack App 생성 (5분)

1. https://api.slack.com/apps → **Create New App** → **From scratch**
2. App 이름: `딸깍봇`, Workspace: `AE Patent AI`
3. 아래 설정 진행:

### OAuth & Permissions → Bot Token Scopes 추가:
```
app_mentions:read
channels:history
channels:read
chat:write
groups:history
groups:read
im:history
im:read
reactions:read
reactions:write
users:read
```

### Event Subscriptions → ON:
- Subscribe to bot events:
  - `app_mention`
  - `message.im`

### Socket Mode → ON:
- Generate App-Level Token (이름: `ddalgak-socket`)
- Scope: `connections:write`
- 생성된 `xapp-...` 토큰 복사

### Install App → Install to Workspace:
- 생성된 `xoxb-...` 봇 토큰 복사


## 2단계: API 키 준비

| 서비스 | 발급 위치 |
|--------|----------|
| Slack Bot Token | 위 1단계에서 발급 (`xoxb-...`) |
| Slack App Token | 위 1단계 Socket Mode (`xapp-...`) |
| Anthropic API Key | https://console.anthropic.com/settings/keys |
| Jira API Token | https://id.atlassian.com/manage-profile/security/api-tokens |
| Notion API Key | https://www.notion.so/my-integrations → 새 통합 생성 |


## 3단계: 실행

```bash
cd projects/ddalgak-bot

# .env 파일 생성 (.env.example 복사 후 값 입력)
cp .env.example .env
# → .env 파일에 토큰값 입력

# 의존성 설치
pip install -r requirements.txt

# 실행
python app.py
```


## 4단계: Slack에서 테스트

1. 아무 채널에 딸깍봇 초대: `/invite @딸깍봇`
2. 멘션으로 테스트: `@딸깍봇 안녕`
3. 작업 지시: `@딸깍봇 Jira에 'UI 개선' 태스크 만들어줘`


## 상시 실행 (선택)

### 방법 A: PM2 (Node.js 프로세스 매니저)
```bash
npm install -g pm2
pm2 start app.py --name ddalgak-bot --interpreter python3
pm2 save && pm2 startup
```

### 방법 B: systemd (Linux)
```bash
sudo tee /etc/systemd/system/ddalgak-bot.service << 'EOF'
[Unit]
Description=딸깍봇 Slack Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/ddalgak-bot
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable ddalgak-bot && sudo systemctl start ddalgak-bot
```

### 방법 C: Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
```
