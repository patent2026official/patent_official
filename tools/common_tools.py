"""범용 도구 — 현재 시간, 요약, 계산 등"""

from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

COMMON_TOOLS = [
    {
        "name": "get_current_time",
        "description": "현재 한국 시간(KST)을 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "calculate",
        "description": "수학 계산을 수행합니다. 파이썬 표현식을 받아 결과를 반환합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "계산할 수식 (예: 2+3*4)"},
            },
            "required": ["expression"],
        },
    },
]


def handle_common_tool(tool_name: str, inp: dict) -> str:
    try:
        if tool_name == "get_current_time":
            now = datetime.now(KST)
            return now.strftime("%Y-%m-%d %H:%M:%S KST (%A)")
        elif tool_name == "calculate":
            # 안전한 수학 계산만 허용
            allowed = set("0123456789+-*/.() ")
            expr = inp["expression"]
            if all(c in allowed for c in expr):
                result = eval(expr)
                return f"{expr} = {result}"
            return "허용되지 않는 문자가 포함된 수식입니다."
        return f"알 수 없는 도구: {tool_name}"
    except Exception as e:
        return f"오류: {e}"
