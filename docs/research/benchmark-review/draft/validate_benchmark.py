"""Validate evidence anchors; no models, imports from app, or database access."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--project',type=Path);a=p.parse_args()
bundle=Path(__file__).resolve().parent
corpus=a.project/'backend/data/raw/knowledge_base' if a.project else bundle/'source-snapshot'
qs=json.loads((bundle/'questions-expanded-draft.json').read_text());seen=set();texts=set();checks=0
for q in qs:
 assert q['id'] not in seen, q['id'];seen.add(q['id'])
 assert q['question'] not in texts,q['question'];texts.add(q['question'])
 e=q['source_evidence'];rel=Path(e['corpus_relative_path']);assert not rel.is_absolute() and '..' not in rel.parts
 data=(corpus/rel).read_bytes();assert hashlib.sha256(data).hexdigest()==e['file_sha256'],f'Source changed: {rel}'
 text=data.decode();assert text[e['start_char']:e['end_char']]==e['exact_excerpt'],q['id']
 assert q['reference_facts'] and q['expected_sections'];checks+=1
print(json.dumps({'status':'passed','questions':checks,'attack_types':len({q['expected_attack_type'] for q in qs}),'checks':['unique IDs','unique question strings','source hashes','exact excerpt offsets','required fields'],'human_review':'pending','new_live_results':False},indent=2))
