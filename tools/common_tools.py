from datetime import datetime, timezone, timedelta
KST = timezone(timedelta(hours=9))
COMMON_TOOLS = [{'name':'get_current_time','description':'현재 한국 시간(KST)을 반환합니다.','input_schema':{'type':'object','properties':{}}}]
def handle_common_tool(name, inp):
    if name == 'get_current_time':
        return datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST (%A)')
    return f'알 수 없는 도구: {name}'
