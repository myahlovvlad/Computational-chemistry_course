"""Prepare a reviewable Stepik request plan. This command never accesses the network."""
import argparse
import hashlib
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit


def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def https_url(value):
    p=urlsplit(value)
    return p.scheme=='https' and bool(p.netloc) and not p.username and not p.password


def make_plan(package, *, only=None, assets=None, file_base=None):
    package=Path(package).resolve(); manifest=load(package/'package.json')
    if manifest['partial']:raise ValueError('Partial package cannot be imported')
    for relative,digest in manifest['files_sha256'].items():
        p=(package/relative).resolve();p.relative_to(package)
        if sha(p)!=digest:raise ValueError('Package changed: '+relative)
    course=load(package/'programm/course.json');assets=assets or {}
    if file_base and not https_url(file_base):raise ValueError('file-base must be HTTPS')
    all_lessons={l['id']:(m,l) for m in course['modules'] for l in m['lessons']}
    selected=set(only or all_lessons)
    if not selected or not selected<=all_lessons.keys():raise ValueError('Unknown lesson selection')
    lessons={id:load(package/id/'lesson.json') for id in all_lessons if id in selected}
    source_links={s['source']:f'@@LESSON:{id}@@/step/{s["position"]}' for id,l in lessons.items() for s in l['steps']}
    missing=set();used={};warnings=[]
    def asset(relative):
        value=assets.get(relative)
        if not value and file_base and relative!='$bundle':
            value=file_base.rstrip('/')+'/'+quote(relative,safe='/._-')
        if not value:
            missing.add(relative);return 'UNRESOLVED_ASSET:'+relative
        if not https_url(value):raise ValueError('Asset URL must be HTTPS: '+relative)
        used[relative]=value;return value
    def rewrite(text,source):
        # Generated Markdown HTML uses quoted attributes; code text is escaped.
        def replace(match):
            prefix,q,reference=match.groups();parts=urlsplit(reference)
            if parts.scheme or reference.startswith('//') or not parts.path:return match[0]
            target=(package/Path(source).parent/unquote(parts.path)).resolve()
            relative=target.relative_to(package).as_posix()
            if not target.is_file():raise ValueError('Missing portable link target: '+relative)
            value=source_links.get(relative) or asset(relative)
            if parts.fragment:value+='#'+parts.fragment
            return prefix+q+escape(value,quote=True)+q
        return re.sub(r'((?:href|src)\s*=\s*)(["\'])(.*?)\2',replace,text)
    operations=[]
    def add(key,endpoint,envelope,data):
        operations.append({'key':key,'method':'POST','endpoint':endpoint,'response_list':endpoint,
                           'payload':{envelope:data}})
    add('course','courses','course',{'title':'[ПРОВЕРКА] '+course['title']})
    for module in course['modules']:
        active=[l for l in module['lessons'] if l['id'] in lessons]
        if not active:continue
        add('section:'+module['id'],'sections','section',{'course':{'$ref':'course'},'title':module['title'],'position':module['position']})
        for position,local in enumerate(active,1):
            id=local['id']
            add('lesson:'+id,'lessons','lesson',{'title':id+'. '+local['title'],'is_public':False})
            add('unit:'+id,'units','unit',{'section':{'$ref':'section:'+module['id']},'lesson':{'$ref':'lesson:'+id},'position':position})
    for id,lesson in lessons.items():
        for step in lesson['steps']:
            if step['block']['name']!='text':raise ValueError('Only text blocks supported')
            text=rewrite(step['block']['text'],step['source'])
            if len(text)>18000:warnings.append({'step':step['local_id'],'reason':'Long text: review screen length before import'})
            add('step:'+step['local_id'],'step-sources','stepSource',{'lesson':{'$ref':'lesson:'+id},'position':step['position'],
                                                                  'block':{'name':'text','text':text}})
        bundle=asset('$bundle')
        books=''.join('<li><code>'+escape(p)+'</code></li>' for p in lesson['notebooks'])
        text='<h2>Практическая работа в Notebook</h2><p>Скачайте и распакуйте весь пакет курса, установите среду по scripts/README.md и откройте нужный Notebook:</p><ul>'+books+'</ul><p><a href="'+escape(bundle,quote=True)+'">Скачать полный пакет</a></p><p>Преподавательские решения не включены. Ответы и научное обоснование передаются отдельно; этот текстовый шаг не проверяет их автоматически.</p>'
        add('download:'+id,'step-sources','stepSource',{'lesson':{'$ref':'lesson:'+id},'position':len(lesson['steps'])+1,'block':{'name':'text','text':text}})
    counts={e:sum(o['endpoint']==e for o in operations) for e in ['courses','sections','lessons','units','step-sources']}
    return {'format':'stepik-api-plan-v1','status':'BLOCKED_ASSETS' if missing else 'READY_FOR_REVIEW',
            'package_sha256':sha(package/'package.json'),'counts':counts,'operations':operations,
            'missing_assets':sorted(missing),'asset_urls':used,'warnings':warnings,
            'assessment_scope':'Text and Notebook download links only; live graders and learner submission workflow NOT_RUN',
            'live_api_status':'NOT_RUN','public_release':'NOT_AUTHORIZED_BY_THIS_PLAN'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('package',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--only',nargs='+');p.add_argument('--assets',type=Path);p.add_argument('--file-base')
    a=p.parse_args();plan=make_plan(a.package,only=a.only,assets=load(a.assets) if a.assets else None,file_base=a.file_base)
    a.out.mkdir(parents=True,exist_ok=False)
    (a.out/'requests.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (a.out/'assets-template.json').write_text(json.dumps({x:'' for x in plan['missing_assets']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:plan[k] for k in ['status','counts','missing_assets','live_api_status']},ensure_ascii=False,indent=2))
    if plan['missing_assets']:raise SystemExit(2)


if __name__=='__main__':main()
