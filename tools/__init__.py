from .jira_tools import JIRA_TOOLS, handle_jira_tool
from .notion_tools import NOTION_TOOLS, handle_notion_tool
from .common_tools import COMMON_TOOLS, handle_common_tool
ALL_TOOLS = JIRA_TOOLS + NOTION_TOOLS + COMMON_TOOLS
def handle_tool_call(name, inp):
    if name.startswith('jira_'): return handle_jira_tool(name, inp)
    elif name.startswith('notion_'): return handle_notion_tool(name, inp)
    else: return handle_common_tool(name, inp)
