from .jira_tools import JIRA_TOOLS, handle_jira_tool
from .notion_tools import NOTION_TOOLS, handle_notion_tool
from .common_tools import COMMON_TOOLS, handle_common_tool

ALL_TOOLS = JIRA_TOOLS + NOTION_TOOLS + COMMON_TOOLS

def handle_tool_call(tool_name: str, tool_input: dict) -> str:
    """도구 호출을 적절한 핸들러로 라우팅"""
    if tool_name.startswith("jira_"):
        return handle_jira_tool(tool_name, tool_input)
    elif tool_name.startswith("notion_"):
        return handle_notion_tool(tool_name, tool_input)
    else:
        return handle_common_tool(tool_name, tool_input)
