#!/usr/bin/env python3
"""Group collaboration protocol 0.1. Python 3.10+, Git; no API or server."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import uuid

class Error(Exception):
    pass

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def write(p, obj):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, encoding='utf-8', errors='replace', capture_output=True)
    if check and p.returncode:
        raise Error(f'{args!r}\n{p.stdout}{p.stderr}')
    return p

def token(s):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', s):
        raise Error('Invalid identifier: ' + s)
    return s

FIELDS = {
    'change_published': 'change_id branch commit summary files_changed interface_changes tests_run known_issues proposed_for_integration',
    'finding': 'summary evidence', 'question': 'question_id text blocking', 'answer': 'question_id text',
    'review': 'change_id verdict summary issues tests_run',
    'test_result': 'scope commit commands automated_result passed failed skipped human_checks_required summary',
    'integration_result': 'change_id target_branch result merge_commit conflicts conflict_resolution_summary verification summary',
    'blocker': 'summary blocking_change_id requested_action',
    'final_candidate': 'canonical_commit candidate_report_path test_evidence known_issues',
    'final_result': 'canonical_commit final_report_path test_evidence known_limitations initiated_by',
}
ENUMS = {'verdict': ['accept','accept_with_changes','reject','needs_more_evidence'],
         'automated_result': ['pass','fail','partial','not_available'],
         'result': ['success','failed','needs_human']}
LISTS = 'related_events files_changed interface_changes tests_run known_issues evidence issues commands human_checks_required conflicts test_evidence known_limitations'.split()
# Finalization evidence has no prescribed element schema in protocol 0.1.
STRING_LISTS = [k for k in LISTS if k != 'test_evidence']
TEXT_FIELDS = 'protocol_version event_id event_type group_id person_id created_at change_id branch commit summary question_id text verdict scope automated_result target_branch result merge_commit conflict_resolution_summary blocking_change_id requested_action canonical_commit candidate_report_path final_report_path initiated_by'.split()

def validate(e):
    if not isinstance(e, dict):
        raise Error('Event must be an object')
    common = 'protocol_version event_id event_type group_id person_id created_at related_events'.split()
    kind = e.get('event_type')
    if not isinstance(kind, str):
        raise Error('event_type must be a string')
    if kind not in FIELDS:
        raise Error('Unsupported event_type')
    for k in common + FIELDS[kind].split():
        if k not in e:
            raise Error('Missing field: ' + k)
    required = common + FIELDS[kind].split()
    for k in TEXT_FIELDS:
        if k in required and not isinstance(e[k], str):
            raise Error(k + ' must be a string')
    if e['protocol_version'] != '0.1':
        raise Error('Unsupported protocol version')
    for k in ['event_id','person_id','group_id']:
        token(e[k])
    try:
        timestamp = dt.datetime.fromisoformat(e['created_at'].replace('Z','+00:00'))
    except ValueError as exc:
        raise Error('created_at must be a valid ISO timestamp') from exc
    if timestamp.tzinfo is None:
        raise Error('Timestamp must include timezone')
    for k in LISTS:
        if k in e and not isinstance(e[k], list):
            raise Error(k + ' must be an array')
        if k in required and k in STRING_LISTS:
            for i, value in enumerate(e[k]):
                if not isinstance(value, str):
                    raise Error(f'{k}[{i}] must be a string')
    for k, values in ENUMS.items():
        if k in e and e[k] not in values:
            raise Error('Invalid ' + k)
    for k in ['blocking','proposed_for_integration']:
        if k in e and type(e[k]) is not bool:
            raise Error(k + ' must be boolean')
    for k in ['passed','failed','skipped']:
        if k in e and (type(e[k]) is not int or e[k] < 0):
            raise Error(k + ' must be a nonnegative integer')
    if kind == 'integration_result':
        if not isinstance(e['verification'], dict) or not all(k in e['verification'] for k in ['build','tests','semantic_review']):
            raise Error('Incomplete verification')
        for k in ['build','tests','semantic_review']:
            if not isinstance(e['verification'][k], str):
                raise Error('verification.' + k + ' must be a string')

class Repo:
    def __init__(self, path='.'):
        self.root = Path(run(['git','rev-parse','--show-toplevel'], path).stdout.strip())
        self.group = self.root / '.group'
        self.cfg = read(self.group / 'group.json')
        self.local = self.group / 'local'
        self.local.mkdir(exist_ok=True)
        self.person = read(self.local / 'identity.json')['person_id']
        if not (self.group / 'members' / (token(self.person)+'.json')).is_file():
            raise Error('Unrecognized member')
        self.canonical = self.cfg['canonical_branch']
        self.remote = 'origin'

    def git(self, *args, check=True):
        return run(['git', *args], self.root, check)

    def sha(self, ref='HEAD'):
        return self.git('rev-parse','--verify',ref+'^{commit}').stdout.strip()

    def branch(self):
        b = self.git('symbolic-ref','--short','HEAD',check=False).stdout.strip()
        if not b:
            raise Error('Detached HEAD is not supported for mutations')
        return b

    def clean(self):
        if self.git('status','--porcelain').stdout.strip():
            raise Error('Working tree is not clean. Commit or stash deliberately first; nothing discarded.')
        if self.git('rev-parse','-q','--verify','MERGE_HEAD',check=False).returncode == 0:
            raise Error('Finish or abort the existing merge first')

    def fetch(self):
        self.git('fetch','--prune',self.remote)

    def push(self):
        self.git('push','-u',self.remote,'HEAD:refs/heads/'+self.branch())

    def ancestor(self, a, b='HEAD'):
        return self.git('merge-base','--is-ancestor',a,b,check=False).returncode == 0

    def events(self):
        # Scan remote feature branches too: published events need not be on main.
        refs = ['HEAD'] + self.git('for-each-ref','--format=%(refname)','refs/remotes/origin').stdout.splitlines()
        changed_events = self.git('log','--all','--diff-filter=MDR','--format=','--name-only','--','.group/events').stdout.strip()
        if changed_events:
            raise Error('Immutable event was changed/deleted in history: '+changed_events)
        found = {}
        for ref in refs:
            paths = self.git('ls-tree','-r','--name-only',ref,'--','.group/events').stdout.splitlines()
            for path in paths:
                if not path.endswith('.json'):
                    continue
                e = json.loads(self.git('show',ref+':'+path).stdout)
                validate(e)
                if e['group_id'] != self.cfg['group_id'] or Path(path).stem != e['event_id']:
                    raise Error('Event identity mismatch: '+path)
                if e['event_id'] in found and found[e['event_id']] != e:
                    raise Error('Immutable event modified: '+e['event_id'])
                found[e['event_id']] = e
        changes = {}
        for e in found.values():
            if e['event_type'] == 'change_published':
                c = e['change_id']
                if c in changes and changes[c] != e['event_id']:
                    raise Error('Duplicate change ID: '+c)
                changes[c] = e['event_id']
        return sorted(found.values(), key=lambda e:(e['created_at'],e['event_id']))

    def emit(self, kind, data, related=None):
        self.clean()
        e = dict(data)
        e.update(protocol_version='0.1', event_id='E-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+self.person+'-'+uuid.uuid4().hex[:12],
                 event_type=kind, group_id=self.cfg['group_id'], person_id=self.person,
                 created_at=now(), related_events=related or [])
        validate(e)
        p = self.group/'events'/(e['event_id']+'.json')
        write(p,e)
        self.git('add','--',str(p))
        self.git('commit','-m','group: '+kind+' '+e['event_id'])
        self.push()
        return e

    def change(self, cid):
        matches = [e for e in self.events() if e['event_type']=='change_published' and e['change_id']==cid]
        if len(matches)!=1:
            raise Error('Change not found or ambiguous: '+cid)
        e=matches[0]
        ref='refs/remotes/origin/'+e['branch']
        self.sha(ref)
        self.sha(e['commit'])
        if not self.ancestor(e['commit'],ref):
            raise Error('Published commit is not on the referenced branch')
        return e

    def status(self):
        self.fetch()
        canonical=self.sha('origin/'+self.canonical)
        ev=self.events()
        seen=read(self.local/'sync.json').get('seen',[]) if (self.local/'sync.json').exists() else []
        return dict(person_id=self.person,group_id=self.cfg['group_id'],branch=self.branch(),commit=self.sha(),
                    canonical_commit=canonical,working_tree=self.git('status','--porcelain').stdout,
                    ahead_behind=self.git('rev-list','--left-right','--count','HEAD...'+canonical).stdout.strip(),
                    new_events=[e for e in ev if e['event_id'] not in seen],
                    published_local_changes=[e for e in ev if e['event_type']=='change_published' and e['person_id']==self.person],
                    test_results=[e for e in ev if e['event_type']=='test_result'],
                    blockers=[e for e in ev if e['event_type']=='blocker'],
                    next_action='Inspect new events and blockers; SYNC before integration. Test evidence applies only to its recorded commit.')

    def checks(self, ref):
        """Run configured argv arrays in a detached, disposable worktree."""
        sha=self.sha(ref)
        config=self.cfg.get('checks',{})
        results=[]
        with tempfile.TemporaryDirectory(prefix='groupctl-') as temp:
            work=Path(temp)/'checkout'
            self.git('worktree','add','--detach',str(work),sha)
            try:
                for category, commands in config.items():
                    for argv in commands:
                        if not isinstance(argv,list) or not argv or not all(isinstance(a,str) for a in argv):
                            raise Error('Check commands must be nonempty argv arrays')
                        argv=[sys.executable if a=='{python}' else a for a in argv]
                        try:
                            p=subprocess.run(argv,cwd=work,text=True,encoding='utf-8',errors='replace',capture_output=True,timeout=120)
                            results.append(dict(category=category,argv=argv,exit_code=p.returncode,output=(p.stdout+p.stderr)[-20000:]))
                        except (OSError,subprocess.TimeoutExpired) as ex:
                            results.append(dict(category=category,argv=argv,exit_code=None,output=str(ex)))
            finally:
                self.git('worktree','remove','--force',str(work))
        result='not_available' if not results else ('partial' if any(x['exit_code'] is None for x in results) else ('fail' if any(x['exit_code'] for x in results) else 'pass'))
        # Counts are check-command counts, never invented unit-test counts.
        return dict(scope=ref,commit=sha,commands=[' '.join(x['argv']) for x in results],automated_result=result,
                    passed=sum(x['exit_code']==0 for x in results),failed=sum(x['exit_code'] not in (0,None) for x in results),
                    skipped=sum(x['exit_code'] is None for x in results),human_checks_required=self.cfg.get('human_checks',[]),
                    summary='Counts refer to check commands; see command_results for actual runner output.',
                    count_unit='check_commands',command_results=results)

    def sync(self, update=False):
        before=self.status()
        validation=None
        if update:
            self.clean()
            self.git('merge','--no-edit','origin/'+self.canonical)
            if self.sha()!=before['commit']:
                validation=self.checks('HEAD')
        ev=self.events()
        write(self.local/'sync.json',dict(seen=[e['event_id'] for e in ev]))
        return dict(before=before,after_commit=self.sha(),validation=validation,
                    note='Agent must inspect relevant interface changes. Unrelated feature branches remain separate.')

    def publish(self, summary, interfaces, issues):
        self.clean()
        if not self.branch().startswith('people/'+self.person+'/'):
            raise Error('PUB requires your own people/<person_id>/<topic> branch')
        self.fetch()
        base='origin/'+self.canonical
        files=self.git('diff','--name-only',base+'...HEAD').stdout.splitlines()
        if not files:
            raise Error('No contribution relative to canonical branch')
        for name in files:
            if re.search(r'(^|/)(\.env($|\.)|id_rsa|id_ed25519|__pycache__|node_modules)(/|$)',name) or name.endswith(('.pem','.key','.pyc')):
                raise Error('Potential secret/generated file: '+name)
        diff=self.git('diff',base+'...HEAD').stdout
        if re.search(r'-----BEGIN .*PRIVATE KEY-----|AKIA[0-9A-Z]{16}',diff):
            raise Error('Potential secret detected')
        checks=self.checks('HEAD')
        if checks['automated_result'] in ('fail','partial'):
            raise Error('Quick validation failed: '+json.dumps(checks))
        if checks['automated_result']=='not_available':
            issues=issues+['No automated checks configured; validation unavailable.']
        commit=self.sha()
        self.push()
        return self.emit('change_published',dict(change_id='C-'+self.person+'-'+uuid.uuid4().hex[:12],branch=self.branch(),commit=commit,
                         summary=summary,files_changed=files,interface_changes=interfaces,tests_run=checks['commands'],
                         known_issues=issues,proposed_for_integration=True,quick_validation=checks))

    def integrate(self,cid):
        self.clean()
        if (self.local/'integration.json').exists():
            raise Error('Previous integration awaits finish-integration')
        self.fetch()
        e=self.change(cid)
        base=self.git('merge-base','HEAD',e['commit']).stdout.strip()
        diff=self.git('diff',base,e['commit']).stdout
        write(self.local/'integration.json',dict(change=e,target_branch=self.branch(),before=self.sha(),conflicts=[]))
        p=self.git('merge','--no-ff','--no-edit',e['commit'],check=False)
        conflicts=self.git('diff','--name-only','--diff-filter=U').stdout.splitlines()
        state=read(self.local/'integration.json'); state['conflicts']=conflicts
        write(self.local/'integration.json',state)
        return dict(git_exit=p.returncode,output=p.stdout+p.stderr,conflicts=conflicts,diff=diff,
                    next_action='Inspect both intents, resolve and commit if needed. Run finish-integration with explicit semantic judgment. Merge alone is not success.')

    def finish(self,semantic,summary):
        self.clean()
        state=read(self.local/'integration.json'); e=state['change']
        if self.branch()!=state['target_branch']:
            raise Error('Wrong integration target branch')
        incorporated=self.ancestor(e['commit'])
        markers=self.git('grep','-n','-I','-E',r'^(<<<<<<< |=======|>>>>>>> )','HEAD','--',':(exclude)specs/*',check=False)
        checks=self.checks('HEAD')
        build=[x for x in checks['command_results'] if x['category']=='build']
        b='not_available' if not build else ('pass' if all(x['exit_code']==0 for x in build) else 'fail')
        result='success' if incorporated and markers.returncode==1 and checks['automated_result']=='pass' and semantic=='pass' else ('needs_human' if semantic=='needs_human' else 'failed')
        event=self.emit('integration_result',dict(change_id=e['change_id'],target_branch=self.branch(),result=result,
             merge_commit=self.sha(),conflicts=state['conflicts'],conflict_resolution_summary=summary,
             verification=dict(build=b,tests=checks['automated_result'],semantic_review=semantic),summary=summary,
             incorporated=incorporated,validation=checks),[e['event_id']])
        (self.local/'integration.json').unlink()
        return event

    def final_prepare(self, decisions, human_checks_done):
        self.clean(); self.fetch()
        if self.branch()!=self.canonical or self.sha()!=self.sha('origin/'+self.canonical):
            raise Error('FINAL must run on the clean, up-to-date canonical branch')
        ev=self.events(); commit=self.sha()
        pending=[e for e in ev if e['event_type']=='change_published' and not self.ancestor(e['commit'],commit)]
        concerns=[e for e in ev if e['event_type']=='blocker' or (e['event_type']=='review' and e['verdict']!='accept') or (e['event_type']=='question' and e['blocking'])]
        needed=[e['change_id'] for e in pending]+[e['event_id'] for e in concerns]
        if any(not isinstance(decisions.get(k),str) or not decisions[k].strip() for k in needed):
            raise Error('Provide reasoned dispositions for pending work/concerns: '+json.dumps(needed))
        checks=self.checks(commit)
        if checks['automated_result']!='pass':
            raise Error('Final validation unavailable or unsuccessful: '+json.dumps(checks))
        if checks['human_checks_required'] and not human_checks_done:
            raise Error('Complete documented human checks before preparing final result')
        test=self.emit('test_result',checks)
        report='\n'.join(['# Group Final Report','','## Assignment',self.cfg['assignment_file'],'','## Result','Accepted group implementation; see assignment and important changes.','','## Canonical Commit',commit,'','## Important Changes']+
            ['- '+e['summary'] for e in ev if e['event_type']=='change_published' and self.ancestor(e['commit'],commit)]+['','## Validation','Test event: '+test['event_id'],json.dumps(checks,ensure_ascii=False,indent=2),'Human checks: '+str(human_checks_done),'','## Known Limitations','Review and complete this section before confirmation.','','## Contributors']+
            ['- '+p.stem for p in sorted((self.group/'members').glob('*.json'))]+['','## Pending Work and Review Dispositions',json.dumps(decisions,ensure_ascii=False,indent=2),''])
        p=self.group/'final'/'candidate.md'; p.parent.mkdir(exist_ok=True); p.write_text(report,encoding='utf-8')
        self.git('add','--',str(p)); self.git('commit','-m','group: final candidate report'); self.push()
        candidate=self.emit('final_candidate',dict(canonical_commit=commit,candidate_report_path='.group/final/candidate.md',test_evidence=[test['event_id']],known_issues=list(decisions.values())))
        write(self.local/'final.json',dict(commit=commit,candidate_event=candidate['event_id'],test_event=test['event_id'],prepared_head=self.sha()))
        return dict(candidate=str(p),canonical_commit=commit,next_action='Human must review and edit candidate, commit/push report edits, then explicitly confirm. Code changes invalidate this candidate.')

    def final_confirm(self, limitations):
        self.clean(); self.fetch()
        state=read(self.local/'final.json')
        if self.branch()!=self.canonical or self.sha()!=self.sha('origin/'+self.canonical):
            raise Error('Canonical branch changed remotely; synchronize and prepare again')
        changed=self.git('diff','--name-only',state['commit'],'HEAD').stdout.splitlines()
        if any(not (p.startswith('.group/events/') or p=='.group/final/candidate.md') for p in changed):
            raise Error('Code/config changed after testing; prepare FINAL again')
        report=(self.group/'final'/'candidate.md').read_text(encoding='utf-8')
        if 'Review and complete this section before confirmation.' in report:
            raise Error('Review candidate and replace limitations placeholder before confirmation')
        p=self.group/'final'; (p/'final_report.md').write_text(report,encoding='utf-8')
        envelope=dict(protocol_version='0.1',group_id=self.cfg['group_id'],canonical_branch=self.canonical,
                      canonical_commit=state['commit'],report_file='.group/final/final_report.md',initiated_by=self.person,
                      created_at=now(),status='completed_with_known_limitations' if limitations else 'completed',known_limitations=limitations)
        write(p/'final.json',envelope)
        self.git('add','--',str(p/'final_report.md'),str(p/'final.json')); self.git('commit','-m','group: confirmed final report'); self.push()
        result=self.emit('final_result',dict(canonical_commit=state['commit'],final_report_path=envelope['report_file'],test_evidence=[state['test_event']],known_limitations=limitations,initiated_by=self.person),[state['candidate_event']])
        (self.local/'final.json').unlink()
        return result

def init(args):
    root=Path(run(['git','rev-parse','--show-toplevel'],'.').stdout.strip())
    group=root/'.group'; token(args.person)
    if args.command=='init':
        if (group/'group.json').exists():
            raise Error('Group already initialized')
        token(args.group)
        run(['git','check-ref-format','--branch',args.canonical],root)
        write(group/'group.json',dict(protocol_version='0.1',group_id=args.group,canonical_branch=args.canonical,assignment_file='.group/assignment/assignment.md',checks={}))
        p=group/'assignment'/'assignment.md'; p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(Path(args.assignment).read_text(encoding='utf-8'),encoding='utf-8')
        for name in ['events','final','local']:
            (group/name).mkdir(exist_ok=True)
        (group/'local'/'.gitkeep').touch()
        with (root/'.gitignore').open('a',encoding='utf-8') as f:
            f.write('\n.group/local/*\n!.group/local/.gitkeep\n__pycache__/\n*.pyc\n')
    elif not (group/'group.json').exists():
        raise Error('Initialize or clone group first')
    member=group/'members'/(args.person+'.json')
    if not member.exists():
        write(member,dict(protocol_version='0.1',person_id=args.person,display_name=args.name,joined_at=now()))
    write(group/'local'/'identity.json',dict(person_id=args.person))
    return dict(person_id=args.person,next_action='Review, commit and push membership/configuration; configure checks before use.')

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    for cmd in ['init','join']:
        a=sub.add_parser(cmd); a.add_argument('--person',required=True); a.add_argument('--name',required=True)
        if cmd=='init':
            a.add_argument('--group',required=True); a.add_argument('--canonical',default='main'); a.add_argument('--assignment',required=True)
    sub.add_parser('status'); sub.add_parser('events')
    a=sub.add_parser('sync'); a.add_argument('--update',action='store_true')
    a=sub.add_parser('publish'); a.add_argument('--summary',required=True); a.add_argument('--interface',action='append',default=[]); a.add_argument('--issue',action='append',default=[])
    a=sub.add_parser('inspect'); a.add_argument('change')
    a=sub.add_parser('integrate'); a.add_argument('change')
    a=sub.add_parser('finish-integration'); a.add_argument('--semantic',choices=['pass','fail','needs_human'],required=True); a.add_argument('--summary',required=True)
    a=sub.add_parser('event'); a.add_argument('payload',help='JSON with event_type and type-specific fields')
    a=sub.add_parser('test'); a.add_argument('scope',nargs='?',default='current')
    a=sub.add_parser('final-prepare'); a.add_argument('--decisions',help='JSON object: pending IDs -> reasoned dispositions'); a.add_argument('--human-checks-done',action='store_true')
    a=sub.add_parser('final-confirm'); a.add_argument('--human-confirmed',action='store_true',required=True); a.add_argument('--limitation',action='append',default=[])
    args=p.parse_args(argv)
    try:
        c=args.command
        if c in ['init','join']:
            out=init(args)
        else:
            r=Repo()
            if c=='status': out=r.status()
            elif c=='events': r.fetch(); out=r.events()
            elif c=='sync': out=r.sync(args.update)
            elif c=='publish': out=r.publish(args.summary,args.interface,args.issue)
            elif c=='inspect':
                r.fetch(); e=r.change(args.change); base=r.git('merge-base','HEAD',e['commit']).stdout.strip(); out=dict(event=e,diff=r.git('diff',base,e['commit']).stdout)
            elif c=='integrate': out=r.integrate(args.change)
            elif c=='finish-integration': out=r.finish(args.semantic,args.summary)
            elif c=='event':
                payload=read(args.payload); kind=payload.pop('event_type'); related=payload.pop('related_events',[])
                if kind in ['change_published','test_result','integration_result','final_candidate','final_result']:
                    raise Error('Use dedicated commands for mechanically verified event types')
                out=r.emit(kind,payload,related)
            elif c=='test':
                r.clean(); r.fetch(); scope=args.scope
                ref='HEAD' if scope=='current' else ('origin/'+r.canonical if scope=='main' else r.change(scope)['commit'])
                out=r.emit('test_result',r.checks(ref))
            elif c=='final-prepare': out=r.final_prepare(read(args.decisions) if args.decisions else {},args.human_checks_done)
            elif c=='final-confirm': out=r.final_confirm(args.limitation)
        print(json.dumps(out,ensure_ascii=False,indent=2)); return 0
    except (Error,OSError,ValueError,KeyError) as ex:
        print('groupctl: '+str(ex),file=sys.stderr); return 1

if __name__=='__main__':
    sys.exit(main())
