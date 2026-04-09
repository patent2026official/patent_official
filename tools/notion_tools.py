import requests, config
HEADERS = {'Authorization':f'Bearer {config.NOTION_API_KEY}','Notion-Version':'2022-06-28','Content-Type':'application/json'}
BASE = 'https://api.notion.com/v1'
NOTION_TOOLS = [
    {'name':'notion_search','description':'Notion에서 페이지/DB를 키워드로 검색합니다.','input_schema':{'type':'object','properties':{'query':{'type':'string','description':'검색 키워드'}},'required':['query']}},
    {'name':'notion_create_task','description':'Tasks DB에 새 태스크를 추가합니다.','input_schema':{'type':'object','properties':{'title':{'type':'string','description':'태스크 제목'},'status':{'type':'string','description':'상태'},'priority':{'type':'string','description':'우선순위'}},'required':['title']}}
]
def handle_notion_tool(name, inp):
    try:
        if name == 'notion_search':
            r = requests.post(f'{BASE}/search',headers=HEADERS,json={'query':inp['query'],'page_size':5}); r.raise_for_status()
            results = r.json().get('results',[])
            if not results: return '검색 결과 없음'
            lines = []
            for p in results:
                title = ''
                for v in p.get('properties',{}).values():
                    if v.get('type')=='title': title=''.join(t.get('plain_text','') for t in v.get('title',[])); break
                lines.append(f'- *{title or \"제목없음\"}* {p.get(\"url\",\"\")}')
            return '\n'.join(lines)
        elif name == 'notion_create_task':
            props = {'이름':{'title':[{'text':{'content':inp['title']}}]}}
            if inp.get('status'): props['상태'] = {'status':{'name':inp['status']}}
            if inp.get('priority'): props['우선순위'] = {'select':{'name':inp['priority']}}
            r = requests.post(f'{BASE}/pages',headers=HEADERS,json={'parent':{'database_id':config.NOTION_TASKS_DB_ID},'properties':props}); r.raise_for_status()
            return f'태스크 생성: *{inp[\"title\"]}* {r.json().get(\"url\",\"\")}'
    except Exception as e: return f'Notion 오류: {e}'
