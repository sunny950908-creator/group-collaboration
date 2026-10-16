"""End-to-end tests use real Git and three clones; no fabricated Git results."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from groupctl import validate, Error
CLI=ROOT/'groupctl.py'

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.base=Path(self.tmp.name)
        self.remote=self.base/'remote.git'
        self.call(self.base,'git','init','--bare','--initial-branch=main',str(self.remote))
        self.a=self.base/'A'; self.b=self.base/'B'; self.c=self.base/'C'
        self.call(self.base,'git','clone',str(self.remote),str(self.a))
        self.identity(self.a,'P17')
        (self.a/'assignment.md').write_text('Build a greeting and count application.\n')
        self.cli(self.a,'init','--group','G-DEMO','--person','P17','--name','Student A','--assignment','assignment.md')
        cfg=json.loads((self.a/'.group/group.json').read_text())
        cfg['checks']={'build':[['{python}','-m','py_compile','app.py']], 'tests':[['{python}','check.py']]}
        (self.a/'.group/group.json').write_text(json.dumps(cfg))
        (self.a/'app.py').write_text('def greet():\n    return "hello"\n\ndef count():\n    return 1\n')
        (self.a/'check.py').write_text('from app import greet, count\nassert isinstance(greet(), str)\nassert count() >= 1\nprint("2 checks passed")\n')
        self.commit(self.a,'initial')
        self.call(self.a,'git','push','-u','origin','main')
        for repo,person in [(self.b,'P22'),(self.c,'P31')]:
            self.call(self.base,'git','clone',str(self.remote),str(repo)); self.identity(repo,person)
            self.cli(repo,'join','--person',person,'--name',person)
            self.commit(repo,'register '+person); self.call(repo,'git','push')
        self.call(self.a,'git','pull','--ff-only')
        self.call(self.b,'git','pull','--ff-only')
        for repo,person in [(self.a,'P17'),(self.b,'P22'),(self.c,'P31')]:
            self.call(repo,'git','checkout','-b','people/'+person+'/work')
            self.call(repo,'git','push','-u','origin','HEAD')

    def tearDown(self): self.tmp.cleanup()
    def call(self,cwd,*args,ok=True):
        p=subprocess.run(args,cwd=cwd,text=True,capture_output=True,encoding='utf-8')
        if ok and p.returncode: self.fail(str(args)+'\n'+p.stdout+p.stderr)
        return p
    def cli(self,cwd,*args,ok=True):
        p=self.call(cwd,sys.executable,str(CLI),*args,ok=ok)
        return json.loads(p.stdout) if ok else p
    def identity(self,repo,person):
        self.call(repo,'git','config','user.name',person)
        self.call(repo,'git','config','user.email',person+'@example.invalid')
    def commit(self,repo,msg):
        self.call(repo,'git','add','.')
        self.call(repo,'git','commit','-m',msg)
    def change(self,repo,old,new,summary):
        p=repo/'app.py'; p.write_text(p.read_text().replace(old,new)); self.commit(repo,summary)
        return self.cli(repo,'publish','--summary',summary)

    def test_full_three_person_conflict_final(self):
        a=self.change(self.a,'"hello"','"hello team"','A improves greeting')
        # B independently changes a separate function; clean merge expected.
        b=self.change(self.b,'return 1','return 2','B updates count')
        sync=self.cli(self.b,'sync')
        self.assertTrue(any(e.get('change_id')==a['change_id'] for e in sync['before']['new_events']))
        self.assertEqual(self.cli(self.b,'integrate',a['change_id'])['git_exit'],0)
        self.assertEqual(self.cli(self.b,'finish-integration','--semantic','pass','--summary','Separate functions; greeting and count contracts preserved')['result'],'success')
        # C independently changes the same greeting line, creating a real conflict.
        c=self.change(self.c,'"hello"','"welcome"','C changes greeting wording')
        conflict=self.cli(self.b,'integrate',c['change_id'])
        self.assertNotEqual(conflict['git_exit'],0)
        self.assertIn('app.py',conflict['conflicts'])
        (self.b/'app.py').write_text('def greet():\n    return "welcome team"\n\ndef count():\n    return 2\n')
        self.commit(self.b,'resolve greeting: preserve welcome and team intent')
        resolved=self.cli(self.b,'finish-integration','--semantic','pass','--summary','Combined both wording intents: welcome team; count remains 2')
        self.assertEqual(resolved['result'],'success')
        self.assertEqual(resolved['conflicts'],['app.py'])
        tested=self.cli(self.b,'test')
        self.assertEqual(tested['automated_result'],'pass')
        self.assertEqual(tested['count_unit'],'check_commands')
        # Explicit acceptance into canonical; INT on a personal branch did not change main.
        self.call(self.b,'git','checkout','main'); self.call(self.b,'git','pull','--ff-only')
        self.assertNotIn('welcome', (self.b/'app.py').read_text())
        self.call(self.b,'git','merge','--no-ff','--no-edit','people/P22/work')
        self.call(self.b,'git','push')
        candidate=self.cli(self.b,'final-prepare')
        self.assertEqual(len(candidate['canonical_commit']),40)
        blocked=self.cli(self.b,'final-confirm','--human-confirmed',ok=False)
        self.assertNotEqual(blocked.returncode,0)
        p=self.b/'.group/final/candidate.md'
        p.write_text(p.read_text().replace('Review and complete this section before confirmation.','Demo only: local bare remote, no GitHub authentication tested.'))
        self.commit(self.b,'human-reviewed candidate'); self.call(self.b,'git','push')
        final=self.cli(self.b,'final-confirm','--human-confirmed','--limitation','Local bare-remote demonstration; GitHub hosting not exercised.')
        self.assertEqual(final['canonical_commit'],candidate['canonical_commit'])
        envelope=json.loads((self.b/'.group/final/final.json').read_text())
        self.assertEqual(envelope['status'],'completed_with_known_limitations')
        final_events=self.cli(self.a,'events')
        self.assertTrue(any(e['event_type']=='final_result' for e in final_events))

    def test_semantic_incompatibility_despite_clean_merge(self):
        # A changes producer; its old tests don't cover B's new consumer.
        (self.a/'app.py').write_text('def greet():\n    return {"text": "hello"}\n\ndef count():\n    return 1\n')
        (self.a/'check.py').write_text('from app import greet, count\nassert isinstance(greet(), dict)\nassert count() >= 1\n')
        self.commit(self.a,'change producer contract')
        a=self.cli(self.a,'publish','--summary','Return object','--interface','greet returns dict instead of str')
        (self.b/'consumer.py').write_text('from app import greet\ndef render():\n    return greet().upper()\n')
        (self.b/'check_consumer.py').write_text('from consumer import render\nassert isinstance(render(),str)\n')
        cfg=json.loads((self.b/'.group/group.json').read_text()); cfg['checks']['tests'].append(['{python}','check_consumer.py'])
        (self.b/'.group/group.json').write_text(json.dumps(cfg)); self.commit(self.b,'consumer assumes string')
        self.assertEqual(self.cli(self.b,'integrate',a['change_id'])['git_exit'],0)
        result=self.cli(self.b,'finish-integration','--semantic','fail','--summary','Consumer upper() incompatible with dictionary return')
        self.assertEqual(result['result'],'failed')
        self.assertEqual(result['verification']['tests'],'fail')

    def test_dirty_work_is_preserved(self):
        p=self.b/'app.py'; p.write_text(p.read_text()+'# unfinished\n')
        response=self.cli(self.b,'sync','--update',ok=False)
        self.assertNotEqual(response.returncode,0)
        self.assertIn('# unfinished',p.read_text())

    def test_no_checks_not_claimed_pass(self):
        cfg=json.loads((self.a/'.group/group.json').read_text()); cfg['checks']={}
        (self.a/'.group/group.json').write_text(json.dumps(cfg)); self.commit(self.a,'remove checks')
        self.assertEqual(self.cli(self.a,'test')['automated_result'],'not_available')

    def test_review_does_not_merge_and_status_is_readonly(self):
        a=self.change(self.a,'"hello"','"hello world"','Greeting')
        old=self.call(self.b,'git','rev-parse','HEAD').stdout
        self.cli(self.b,'status')
        self.assertEqual(old,self.call(self.b,'git','rev-parse','HEAD').stdout)
        payload=self.base/'review.json'; payload.write_text(json.dumps(dict(event_type='review',change_id=a['change_id'],verdict='accept',summary='Reviewed actual diff',issues=[],tests_run=[])))
        self.cli(self.b,'event',str(payload))
        self.assertIn('"hello"',(self.b/'app.py').read_text())

    def test_pending_change_blocks_final(self):
        self.change(self.a,'"hello"','"hello world"','Unintegrated important work')
        self.call(self.c,'git','checkout','main')
        response=self.cli(self.c,'final-prepare',ok=False)
        self.assertNotEqual(response.returncode,0)
        self.assertIn('dispositions',response.stderr)

    def test_final_rejects_code_changed_after_candidate(self):
        self.call(self.c,'git','checkout','main')
        self.cli(self.c,'final-prepare')
        p=self.c/'app.py'; p.write_text(p.read_text()+'# new change\n'); self.commit(self.c,'changed after final test'); self.call(self.c,'git','push')
        response=self.cli(self.c,'final-confirm','--human-confirmed',ok=False)
        self.assertIn('Code/config changed',response.stderr)

    def test_secret_filename_refused(self):
        (self.a/'.env').write_text('DEMO_VALUE=not_a_real_secret\n'); self.commit(self.a,'accidental env')
        response=self.cli(self.a,'publish','--summary','oops',ok=False)
        self.assertNotEqual(response.returncode,0); self.assertIn('Potential secret',response.stderr)

class Validation(unittest.TestCase):
    def test_missing_fields_and_invalid_enums(self):
        with self.assertRaises(Error): validate({'event_type':'review'})
        with self.assertRaises(Error): validate({'event_type':'invented'})

if __name__=='__main__': unittest.main(verbosity=2)
