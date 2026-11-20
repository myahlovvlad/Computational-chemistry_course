"""Execute an explicitly approved text-import plan; default is offline inspection."""
import argparse
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request
from datetime import datetime,timezone

HOST='https://stepik.org'
ALLOWED={'courses':'course','sections':'section','lessons':'lesson','units':'unit','step-sources':'stepSource'}


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    os.replace(temporary,path)


class Client:
    def __init__(self):
        client_id=os.environ.get('STEPIK_CLIENT_ID') or input('Stepik Client ID: ')
        secret=getpass.getpass('Stepik Client Secret (не сохраняется): ')
        data=urllib.parse.urlencode({'grant_type':'client_credentials'}).encode()
        basic=base64.b64encode((client_id+':'+secret).encode()).decode()
        request=urllib.request.Request(HOST+'/oauth2/token/',data=data,
                    headers={'Authorization':'Basic '+basic,'Content-Type':'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(request,timeout=30) as response:token=json.load(response)
        self.token=token['access_token']

    def request(self,method,endpoint,payload=None):
        data=json.dumps(payload,ensure_ascii=False).encode() if payload is not None else None
        request=urllib.request.Request(HOST+'/api/'+endpoint,data=data,method=method,
                   headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=45) as response:return json.load(response)


def resolve(value,objects):
    if isinstance(value,dict):
        if set(value)=={'$ref'}:return objects[value['$ref']]['id']
        return {k:resolve(v,objects) for k,v in value.items()}
    if isinstance(value,list):return [resolve(v,objects) for v in value]
    if isinstance(value,str):
        return re.sub(r'@@LESSON:(M\d{2}-L\d{2})@@',lambda m:HOST+'/lesson/'+str(objects['lesson:'+m[1]]['id']),value)
    return value


def send(plan,path,*,course_only,course_ready,client):
    digest=hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    state=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {'plan_sha256':digest,'objects':{},'pending':None}
    if state['plan_sha256']!=digest:raise ValueError('Plan changed: use a new state file and review target')
    if state.get('pending'):raise RuntimeError('Uncertain previous POST; reconcile pending in Stepik before retrying')
    operations=plan['operations'][:1] if course_only else plan['operations']
    if not course_only:
        if not course_ready or 'course' not in state['objects']:
            raise ValueError('Create the empty course first; confirm draft/access settings before importing content')
        course_id=state['objects']['course']['id']
        remote=client.request('GET',f'courses/{course_id}')['courses'][0]
        if remote['title']!=plan['operations'][0]['payload']['course']['title']:
            raise ValueError('Remote course title differs; review target before proceeding')
        known_sections={v['id'] for k,v in state['objects'].items() if k.startswith('section:')}
        if set(remote.get('sections',[]))-known_sections:raise ValueError('Target contains sections outside this import')
        for value in state['objects'].values():
            if value['endpoint']=='lessons':
                lesson=client.request('GET',f'lessons/{value["id"]}')['lessons'][0]
                if lesson.get('is_public') is not False:raise ValueError('Existing lesson privacy not confirmed; review access in Stepik')
    for operation in operations:
        endpoint=operation['endpoint'];key=operation['key']
        if endpoint not in ALLOWED or operation['method']!='POST' or set(operation['payload'])!={ALLOWED[endpoint]}:
            raise ValueError('Unsupported operation')
        if key in state['objects']:continue
        payload=resolve(operation['payload'],state['objects'])
        if '@@LESSON:' in json.dumps(payload) or 'UNRESOLVED_ASSET:' in json.dumps(payload):raise ValueError('Unresolved reference')
        state['pending']={'key':key,'endpoint':endpoint,'payload':payload,
                          'started_utc':datetime.now(timezone.utc).isoformat()};save(path,state)
        response=client.request('POST',endpoint,payload)
        rows=response[endpoint]
        if len(rows)!=1 or not isinstance(rows[0]['id'],int):raise ValueError('Unexpected response; reconcile pending')
        state['objects'][key]={'id':rows[0]['id'],'endpoint':endpoint}
        state['pending']=None;save(path,state)
        print(key,rows[0]['id'])
        if endpoint=='lessons' and rows[0].get('is_public') is not False:
            raise ValueError('Created lesson privacy not confirmed; stop and review access in Stepik')
    if not course_only:state['status']='IMPORTED_NOT_VERIFIED'
    elif len(state['objects'])==1:state['status']='EMPTY_COURSE_CREATED'
    save(path,state)
    return state


def verify(plan,state,client):
    digest=hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if state['plan_sha256']!=digest:raise ValueError('Plan changed')
    missing=[];differences=[];checked=0
    for op in plan['operations']:
        key=op['key']
        if key not in state['objects']:missing.append(key);continue
        identity=state['objects'][key]
        actual=client.request('GET',op['endpoint']+'/'+str(identity['id']))[op['endpoint']][0]
        expected=next(iter(resolve(op['payload'],state['objects']).values()))
        for field,value in expected.items():
            if field=='block':
                for part in ['name','text']:
                    if actual.get('block',{}).get(part)!=value.get(part):differences.append({'key':key,'field':'block.'+part})
            elif actual.get(field)!=value:differences.append({'key':key,'field':field})
        checked+=1
    return {'status':'REVIEW_REQUIRED' if missing or differences or state.get('pending') else 'PASS',
            'scope':'GET round-trip fields only; browser rendering, learner permissions, assets and graders need separate checks',
            'objects_checked':checked,'missing':missing,'differences':differences,'pending':state.get('pending',{}),
            'publication':'NOT_PERFORMED'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('plan',type=Path);p.add_argument('--state',type=Path,required=True)
    p.add_argument('--apply',action='store_true');p.add_argument('--course-only',action='store_true')
    p.add_argument('--course-ready',action='store_true',help='User checked course remains a draft and access settings')
    p.add_argument('--verify',action='store_true');p.add_argument('--report',type=Path)
    a=p.parse_args();plan=json.loads(a.plan.read_text(encoding='utf-8'))
    if a.verify:
        if not a.report or a.report.exists():raise SystemExit('Choose a new --report path')
        state=json.loads(a.state.read_text(encoding='utf-8'))
        report=verify(plan,state,Client());save(a.report,report)
        print(json.dumps(report,ensure_ascii=False,indent=2))
        if report['status']!='PASS':raise SystemExit(2)
        return
    if not a.apply:
        print(json.dumps({'mode':'OFFLINE','status':plan['status'],'counts':plan['counts'],'action':'No request sent'},indent=2));return
    if plan['status']!='READY_FOR_REVIEW':raise SystemExit('BLOCKED: unresolved assets')
    send(plan,a.state,course_only=a.course_only,course_ready=a.course_ready,client=Client())


if __name__=='__main__':main()
