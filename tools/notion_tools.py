"""Notion 연동 도구 — 페이지/DB 조회, 생성, 수정"""

import json
import requests
import config

HEADERS = {
    "Authorization": f"Bearer {config.NOTION_API_KEY}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}
BASE = "https://api.notion.com/v1"

# ── Tool 정의 ───────────────────────────────────────────────────

NOTION_TOOLS = [
    {
        "name": "notion_search",
        "description": "Notion에서 페이지/DB를 키워드로 검색합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "검색 키워드"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "notion_get_page",
        "description": "Notion 페이지의 내용을 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "page_id": {"type": "string", "description": "페이지 ID (UUID)"},
            },
            "required": ["page_id"],
        },
    },
    {
        "name": "notion_create_task",
        "description": "Tasks DB에 새 태스크를 추가합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "태스크 제목"},
                "status": {
                    "type": "string",
                    "enum": ["시작 전", "진행 중", "완료", "보류"],
                    "description": "상태 (기본: 시작 전)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["P0-긴급", "P1-높음", "P2-보통", "P3-낮음"],
                    "description": "우선순위 (기본: P2-보통)",
                },
                "category": {
                    "type": "string",
                    "enum": ["기획", "개발", "디자인", "테스트", "배포", "문서화"],
                    "description": "구분 (선택)",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "notion_query_tasks",
        "description": "Tasks DB에서 필터 조건으로 태스크를 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "상태 필터 (선택)"},
                "priority": {"type": "string", "description": "우선순위 필터 (선택)"},
                "week": {"type": "string", "description": "주차 필터 (예: W15 (04/07~04/11))"},
            },
        },
    },
    {
        "name": "notion_create_page",
        "description": "Notion에 새 페이지를 생성합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "parent_page_id": {"type": "string", "description": "상위 페이지 ID"},
                "title": {"type": "string", "description": "페이지 제목"},
                "content": {"type": "string", "description": "페이지 내용 (마크다운)"},
            },
            "required": ["parent_page_id", "title"],
        },
    },
]


# ── 핸들러 ──────────────────────────────────────────────────────

def handle_notion_tool(tool_name: str, inp: dict) -> str:
    try:
        if tool_name == "notion_search":
            return _search(inp)
        elif tool_name == "notion_get_page":
            return _get_page(inp)
        elif tool_name == "notion_create_task":
            return _create_task(inp)
        elif tool_name == "notion_query_tasks":
            return _query_tasks(inp)
        elif tool_name == "notion_create_page":
            return _create_page(inp)
        return f"알 수 없는 도구: {tool_name}"
    except Exception as e:
        return f"Notion 오류: {e}"


def _search(inp: dict) -> str:
    r = requests.post(f"{BASE}/search", headers=HEADERS, json={
        "query": inp["query"], "page_size": 5,
    })
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return "검색 결과 없음"
    lines = []
    for p in results:
        obj_type = p["object"]
        pid = p["id"]
        title = ""
        if obj_type == "page":
            props = p.get("properties", {})
            for v in props.values():
                if v.get("type") == "title":
                    title = "".join(t.get("plain_text", "") for t in v.get("title", []))
                    break
        elif obj_type == "database":
            title = "".join(t.get("plain_text", "") for t in p.get("title", []))
        url = p.get("url", "")
        lines.append(f"• [{obj_type}] *{title or '제목 없음'}*\n  {url}")
    return "\n".join(lines)


def _get_page(inp: dict) -> str:
    pid = inp["page_id"].replace("-", "")
    # 페이지 속성
    r = requests.get(f"{BASE}/pages/{pid}", headers=HEADERS)
    r.raise_for_status()
    page = r.json()
    title = ""
    for v in page.get("properties", {}).values():
        if v.get("type") == "title":
            title = "".join(t.get("plain_text", "") for t in v.get("title", []))
            break

    # 블록 내용 (첫 20개)
    r2 = requests.get(f"{BASE}/blocks/{pid}/children?page_size=20", headers=HEADERS)
    r2.raise_for_status()
    blocks = r2.json().get("results", [])
    content_lines = []
    for b in blocks:
        btype = b["type"]
        rich = b.get(btype, {}).get("rich_text", [])
        text = "".join(t.get("plain_text", "") for t in rich)
        if text:
            content_lines.append(text)

    content = "\n".join(content_lines[:10]) or "(내용 없음)"
    return f"*{title}*\n{content}\n링크: {page.get('url', '')}"


def _create_task(inp: dict) -> str:
    properties = {
        "이름": {"title": [{"text": {"content": inp["title"]}}]},
    }
    if inp.get("status"):
        properties["상태"] = {"status": {"name": inp["status"]}}
    if inp.get("priority"):
        properties["우선순위"] = {"select": {"name": inp["priority"]}}
    if inp.get("category"):
        properties["구분"] = {"select": {"name": inp["category"]}}

    r = requests.post(f"{BASE}/pages", headers=HEADERS, json={
        "parent": {"database_id": config.NOTION_TASKS_DB_ID},
        "properties": properties,
    })
    r.raise_for_status()
    data = r.json()
    return f"태스크 생성 완료: *{inp['title']}*\n링크: {data.get('url', '')}"


def _query_tasks(inp: dict) -> str:
    filters = []
    if inp.get("status"):
        filters.append({"property": "상태", "status": {"equals": inp["status"]}})
    if inp.get("priority"):
        filters.append({"property": "우선순위", "select": {"equals": inp["priority"]}})
    if inp.get("week"):
        filters.append({"property": "주차", "select": {"equals": inp["week"]}})

    body = {"page_size": 20}
    if len(filters) == 1:
        body["filter"] = filters[0]
    elif len(filters) > 1:
        body["filter"] = {"and": filters}

    r = requests.post(f"{BASE}/databases/{config.NOTION_TASKS_DB_ID}/query", headers=HEADERS, json=body)
    r.raise_for_status()
    results = r.json().get("results", [])
    if not results:
        return "조건에 맞는 태스크 없음"

    lines = []
    for p in results:
        props = p["properties"]
        title = "".join(t.get("plain_text", "") for t in props.get("이름", {}).get("title", []))
        status = props.get("상태", {}).get("status", {}).get("name", "")
        priority = props.get("우선순위", {}).get("select", {})
        pri_name = priority.get("name", "") if priority else ""
        lines.append(f"• [{status}] {pri_name} *{title}*")
    return f"태스크 {len(results)}건:\n" + "\n".join(lines)


def _create_page(inp: dict) -> str:
    children = []
    if inp.get("content"):
        for line in inp["content"].split("\n"):
            if line.strip():
                children.append({
                    "object": "block", "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]},
                })

    r = requests.post(f"{BASE}/pages", headers=HEADERS, json={
        "parent": {"page_id": inp["parent_page_id"]},
        "properties": {"title": [{"text": {"content": inp["title"]}}]},
        "children": children[:100],
    })
    r.raise_for_status()
    data = r.json()
    return f"페이지 생성 완료: *{inp['title']}*\n링크: {data.get('url', '')}"
