import hashlib,json
from pathlib import Path
import sys,tempfile,unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stepik_plan import make_plan
from stepik_send import send,verify


class FakeClient:
    def __init__(self):self.objects={};self.next_id=100;self.posts=0;self.lose_next_response=False
    def request(self,method,endpoint,payload=None):
        if method=='GET':
            kind,id=endpoint.split('/');return {kind:[self.objects[kind][int(id)]]}
        self.posts+=1;self.next_id+=1
        value=dict(next(iter(payload.values())),id=self.next_id)
        if endpoint=='courses':value['sections']=[]
        if endpoint=='sections':self.objects['courses'][value['course']]['sections'].append(self.next_id)
        self.objects.setdefault(endpoint,{})[self.next_id]=value
        if self.lose_next_response:
            self.lose_next_response=False;raise TimeoutError('Server may have accepted POST')
        return {endpoint:[value]}


class StepikPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        def write(name,value):
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text(json.dumps(value) if isinstance(value,dict) else value)
        lessons=[{'id':f'M01-L0{i}','title':f'Lesson {i}'} for i in [1,2]]
        write('programm/course.json',{'title':'Test','modules':[{'id':'M01','position':1,'title':'Module','lessons':lessons}]})
        for i in [1,2]:
            id=f'M01-L0{i}';source=f'theory/L0{i}.md'
            write(source,'source')
            text='<p><a href="L02.md#criterion">next</a><img src="../media/plot.svg"></p>' if i==1 else '<p>Second</p>'
            write(id+'/lesson.json',{'steps':[{'source':source,'position':1,'local_id':id+'-S01','block':{'name':'text','text':text}}],
                                      'notebooks':[id+'/case.ipynb',id+'/lab.ipynb']})
        write('media/plot.svg','<svg/>')
        hashes={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        write('package.json',{'partial':False,'files_sha256':hashes})
    def tearDown(self):self.temp.cleanup()
    def ready(self):return make_plan(self.root,assets={'$bundle':'https://example.org/course.zip'},file_base='https://example.org/frozen/')
    def test_blocked_assets_and_lesson_links(self):
        plan=make_plan(self.root)
        self.assertEqual(plan['status'],'BLOCKED_ASSETS')
        self.assertEqual(plan['missing_assets'],['$bundle','media/plot.svg'])
        text=next(o for o in plan['operations'] if o['key']=='step:M01-L01-S01')['payload']['stepSource']['block']['text']
        self.assertIn('@@LESSON:M01-L02@@/step/1#criterion',text)
    def test_export_counts_and_private_lessons(self):
        plan=self.ready();self.assertEqual(plan['counts'],{'courses':1,'sections':1,'lessons':2,'units':2,'step-sources':4})
        for op in plan['operations']:
            if op['endpoint']=='lessons':self.assertFalse(op['payload']['lesson']['is_public'])
    def test_tampered_package_rejected(self):
        (self.root/'media/plot.svg').write_text('changed')
        with self.assertRaisesRegex(ValueError,'Package changed'):self.ready()
    def test_pilot_starts_at_first_section_position(self):
        source=self.root/'programm/course.json'
        course=json.loads(source.read_text());course['modules'][0]['position']=7
        source.write_text(json.dumps(course))
        path=self.root/'package.json';manifest=json.loads(path.read_text())
        manifest['files_sha256']['programm/course.json']=hashlib.sha256(source.read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))
        plan=make_plan(self.root,only=['M01-L02'],assets={'$bundle':'https://example.org/course.zip'})
        section=next(o for o in plan['operations'] if o['endpoint']=='sections')
        self.assertEqual(section['payload']['section']['position'],1)
    def test_resume_does_not_duplicate_posts_and_resolves_links(self):
        plan=self.ready();state=self.root/'state.json';client=FakeClient()
        send(plan,state,course_only=True,course_ready=False,client=client)
        result=send(plan,state,course_only=False,course_ready=True,client=client)
        count=client.posts
        send(plan,state,course_only=False,course_ready=True,client=client)
        self.assertEqual(client.posts,count)
        self.assertEqual(result['status'],'IMPORTED_NOT_VERIFIED')
        texts=[v['block']['text'] for v in client.objects['step-sources'].values()]
        self.assertTrue(any('https://stepik.org/lesson/' in t for t in texts))
        self.assertFalse(any('@@LESSON:' in t for t in texts))
        self.assertEqual(verify(plan,result,client)['status'],'PASS')
        source=next(iter(client.objects['step-sources'].values()))
        source['block']['text']='server altered text'
        self.assertEqual(verify(plan,result,client)['status'],'REVIEW_REQUIRED')
    def test_uncertain_post_never_retried(self):
        client=FakeClient();client.lose_next_response=True;state=self.root/'uncertain.json'
        with self.assertRaises(TimeoutError):send(self.ready(),state,course_only=True,course_ready=False,client=client)
        with self.assertRaisesRegex(RuntimeError,'Uncertain'):send(self.ready(),state,course_only=True,course_ready=False,client=client)
        self.assertEqual(client.posts,1)
    def test_unknown_remote_section_blocks_resume(self):
        client=FakeClient();state=self.root/'state.json';plan=self.ready()
        result=send(plan,state,course_only=True,course_ready=False,client=client)
        client.objects['courses'][result['objects']['course']['id']]['sections']=[999]
        with self.assertRaisesRegex(ValueError,'outside'):send(plan,state,course_only=False,course_ready=True,client=client)


if __name__=='__main__':unittest.main()
