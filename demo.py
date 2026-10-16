#!/usr/bin/env python3
"""Reproduce the three-clone scenario and preserve its Git history. No Internet used."""
import argparse
import json
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).parent/'tests'))
from test_workflow import Workflow

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',default='demo-output')
a=p.parse_args()
target=Path(a.output).resolve()
if target.exists():
    p.error('Output must not exist; choose a fresh directory.')
case=Workflow('test_full_three_person_conflict_final')
try:
    case.setUp()
    case.test_full_three_person_conflict_final()
    shutil.copytree(case.base,target)
    for name in ['A','B','C']:
        case.call(target/name,'git','remote','set-url','origin',str(target/'remote.git'))
    events=case.cli(target/'B','events')
    (target/'events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
    graph=case.call(target/'B','git','log','--all','--graph','--oneline','--decorate').stdout
    (target/'git-history.txt').write_text(graph,encoding='utf-8')
    (target/'DEMO-NOTICE.txt').write_text('This is a scripted simulation using 3 local clones and a local bare remote.\nConflict resolution and human confirmation are simulated, not real human/AI sessions.\nUse docs/GITHUB_DEMO.md for the live GitHub + AI demonstration.\n',encoding='utf-8')
    print('Demo passed. Repositories, events and Git history: '+str(target))
finally:
    if hasattr(case,'tmp'): case.tearDown()
