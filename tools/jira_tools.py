"""Jira 연동 도구 — 이슈 CRUD, 검색, 상태 변경"""

import json
import requests
from requests.auth import HTTPBasicAuth
import config

auth = HTTPBasicAuth(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
headers = {"Accept": "application/json", "Content-Type": "application/json"}
BASE = config.JIRA_BASE_URL

# ── Tool 정의 (Claude tool_use 스키마) ──────────────────────────

JIRA_TOOLS = [
    {
        "name": "jira_create_issue",
        "description": "Jira에 새 이슈(에픽/태스크/버그/스토리)를 생성합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "이슈 제목"},
                "issue_type": {
                    "type": "string",
                    "enum": ["Epic", "Task", "Bug", "Story"],
                    "description": "이슈 유형",
                },
                "description": {"type": "string", "description": "이슈 설명 (선택)"},
                "priority": {
                    "type": "string",
                    "enum": ["Highest", "High", "Medium", "Low", "Lowest"],
                    "description": "우선순위 (선택, 기본 Medium)",
                },
                "parent_key": {
                    "type": "string",
                    "description": "상위 에픽 키 (예: SCRUM-5). 태스크를 에픽 하위로 만들 때 사용",
                },
            },
            "required": ["summary", "issue_type"],
        },
    },
    {
        "name": "jira_search_issues",
        "description": "JQL로 Jira 이슈를 검색합니다. 예: 'project=SCRUM AND status=\"To Do\"'",
        "input_schema": {
            "type": "object",
            "properties": {
                "jql": {"type": "string", "description": "JQL 쿼리"},
                "max_results": {"type": "integer", "description": "최대 결과 수 (기본 10)"},
            },
            "required": ["jql"],
        },
    },
    {
        "name": "jira_get_issue",
        "description": "특정 Jira 이슈의 상세 정보를 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "이슈 키 (예: SCRUM-5)"},
            },
            "required": ["issue_key"],
        },
    },
    {
        "name": "jira_update_issue",
        "description": "Jira 이슈의 필드(제목, 설명, 우선순위 등)를 수정합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "이슈 키"},
                "summary": {"type": "string", "description": "새 제목 (선택)"},
                "description": {"type": "string", "description": "새 설명 (선택)"},
                "priority": {"type": "string", "description": "새 우선순위 (선택)"},
            },
            "required": ["issue_key"],
        },
    },
    {
        "name": "jira_transition_issue",
        "description": "Jira 이슈의 상태를 변경합니다 (예: To Do → In Progress → Done).",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "이슈 키"},
                "status": {
                    "type": "string",
                    "description": "변경할 상태명 (예: In Progress, Done)",
                },
            },
            "required": ["issue_key", "status"],
        },
    },
]


# ── 핸들러 ──────────────────────────────────────────────────────

def handle_jira_tool(tool_name: str, inp: dict) -> str:
    try:
        if tool_name == "jira_create_issue":
            return _create_issue(inp)
        elif tool_name == "jira_search_issues":
            return _search_issues(inp)
        elif tool_name == "jira_get_issue":
            return _get_issue(inp)
        elif tool_name == "jira_update_issue":
            return _update_issue(inp)
        elif tool_name == "jira_transition_issue":
            return _transition_issue(inp)
        return f"알 수 없는 도구: {tool_name}"
    except Exception as e:
        return f"Jira 오류: {e}"


def _create_issue(inp: dict) -> str:
    fields = {
        "project": {"key": config.JIRA_PROJECT_KEY},
        "summary": inp["summary"],
        "issuetype": {"name": inp["issue_type"]},
    }
    if inp.get("description"):
        fields["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": inp["description"]}]}],
        }
    if inp.get("priority"):
        fields["priority"] = {"name": inp["priority"]}
    if inp.get("parent_key"):
        fields["parent"] = {"key": inp["parent_key"]}

    r = requests.post(f"{BASE}/rest/api/3/issue", headers=headers, auth=auth, json={"fields": fields})
    r.raise_for_status()
    data = r.json()
    key = data["key"]
    return f"이슈 생성 완료: *{key}* — {inp['summary']}\n링크: {BASE}/browse/{key}"


def _search_issues(inp: dict) -> str:
    params = {"jql": inp["jql"], "maxResults": inp.get("max_results", 10), "fields": "summary,status,priority,assignee"}
    r = requests.get(f"{BASE}/rest/api/3/search", headers=headers, auth=auth, params=params)
    r.raise_for_status()
    issues = r.json().get("issues", [])
    if not issues:
        return "검색 결과 없음"
    lines = []
    for i in issues:
        key = i["key"]
        s = i["fields"]["summary"]
        status = i["fields"]["status"]["name"]
        lines.append(f"• *{key}* [{status}] {s}")
    return f"검색 결과 ({len(issues)}건):\n" + "\n".join(lines)


def _get_issue(inp: dict) -> str:
    key = inp["issue_key"]
    r = requests.get(f"{BASE}/rest/api/3/issue/{key}", headers=headers, auth=auth)
    r.raise_for_status()
    f = r.json()["fields"]
    return (
        f"*{key}* — {f['summary']}\n"
        f"유형: {f['issuetype']['name']} | 상태: {f['status']['name']} | "
        f"우선순위: {f.get('priority', {}).get('name', 'N/A')}\n"
        f"링크: {BASE}/browse/{key}"
    )


def _update_issue(inp: dict) -> str:
    key = inp["issue_key"]
    fields = {}
    if inp.get("summary"):
        fields["summary"] = inp["summary"]
    if inp.get("description"):
        fields["description"] = {
            "type": "doc", "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": inp["description"]}]}],
        }
    if inp.get("priority"):
        fields["priority"] = {"name": inp["priority"]}
    r = requests.put(f"{BASE}/rest/api/3/issue/{key}", headers=headers, auth=auth, json={"fields": fields})
    r.raise_for_status()
    return f"*{key}* 수정 완료"


def _transition_issue(inp: dict) -> str:
    key = inp["issue_key"]
    target = inp["status"].lower()

    # 가능한 transition 조회
    r = requests.get(f"{BASE}/rest/api/3/issue/{key}/transitions", headers=headers, auth=auth)
    r.raise_for_status()
    transitions = r.json()["transitions"]

    tid = None
    for t in transitions:
        if t["name"].lower() == target or t["to"]["name"].lower() == target:
            tid = t["id"]
            break
    if not tid:
        avail = ", ".join(t["name"] for t in transitions)
        return f"'{inp['status']}' 상태로 변경 불가. 가능한 상태: {avail}"

    r = requests.post(
        f"{BASE}/rest/api/3/issue/{key}/transitions",
        headers=headers, auth=auth,
        json={"transition": {"id": tid}},
    )
    r.raise_for_status()
    return f"*{key}* 상태 변경 완료 → {inp['status']}"
