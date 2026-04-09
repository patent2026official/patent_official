import requests
from requests.auth import HTTPBasicAuth
import config
auth = HTTPBasicAuth(config.JIRA_EMAIL, config.JIRA_API_TOKEN)
headers = {'Accept':'application/json','Content-Type':'application/json'}
BASE = config.JIRA_BASE_URL
JIRA_TOOLS = [
    {'name':'jira_create_issue','description':'Jira에 새 이슈를 생성합니다.','input_schema':{'type':'object','properties':{'summary':{'type':'string','description':'이슈 제목'},'issue_type':{'type':'string','enum':['Epic','Task','Bug','Story'],'description':'이슈 유형'},'description':{'type':'string','description':'이슈 설명'},'priority':{'type':'string','enum':['Highest','High','Medium','Low','Lowest'],'description':'우선순위'},'parent_key':{'type':'string','description':'상위 에픽 키'}},'required':['summary','issue_type']}},
    {'name':'jira_search_issues','description':'JQL로 Jira 이슈를 검색합니다.','input_schema':{'type':'object','properties':{'jql':{'type':'string','description':'JQL 쿼리'}},'required':['jql']}},
    {'name':'jira_transition_issue','description':'Jira 이슈의 상태를 변경합니다.','input_schema':{'type':'object','properties':{'issue_key':{'type':'string','description':'이슈 키'},'status':{'type':'string','description':'변경할 상태명'}},'required':['issue_key','status']}}
]
def handle_jira_tool(name, inp):
    try:
        if name == 'jira_create_issue':
            fields = {'project':{'key':config.JIRA_PROJECT_KEY},'summary':inp['summary'],'issuetype':{'name':inp['issue_type']}}
            if inp.get('priority'): fields['priority'] = {'name':inp['priority']}
            if inp.get('parent_key'): fields['parent'] = {'key':inp['parent_key']}
            r = requests.post(f'{BASE}/rest/api/3/issue',headers=headers,auth=auth,json={'fields':fields}); r.raise_for_status()
            key = r.json()['key']
            return f'이슈 생성 완료: *{key}* - {inp[\"summary\"]}\n링크: {BASE}/browse/{key}'
        elif name == 'jira_search_issues':
            r = requests.get(f'{BASE}/rest/api/3/search',headers=headers,auth=auth,params={'jql':inp['jql'],'maxResults':10,'fields':'summary,status,priority'}); r.raise_for_status()
            issues = r.json().get('issues',[])
            if not issues: return '검색 결과 없음'
            return '\n'.join([f'- *{i[\"key\"]}* [{i[\"fields\"][\"status\"][\"name\"]}] {i[\"fields\"][\"summary\"]}' for i in issues])
        elif name == 'jira_transition_issue':
            r = requests.get(f'{BASE}/rest/api/3/issue/{inp[\"issue_key\"]}/transitions',headers=headers,auth=auth); r.raise_for_status()
            tid = next((t['id'] for t in r.json()['transitions'] if t['name'].lower()==inp['status'].lower()),None)
            if not tid: return f'상태 변경 불가: {inp[\"status\"]}'
            requests.post(f'{BASE}/rest/api/3/issue/{inp[\"issue_key\"]}/transitions',headers=headers,auth=auth,json={'transition':{'id':tid}})
            return f'*{inp[\"issue_key\"]}* 상태 변경 완료'
    except Exception as e: return f'Jira 오류: {e}'
