import copy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def build_state(before):
 d=json.loads((P/'decision.json').read_text());assert before['current_stage']==d['predecessor']
 after=copy.deepcopy(before)
 after.update(current_stage=d['publication_id'],last_updated=d['published_at'],safe_to_proceed='YES WITH LIMITATIONS',proceed_scope=d['scope'])
 after[d['state_field']]=d
 after['methodological_decisions'].extend(json.loads((P/'decision_ledger.json').read_text())['decisions'])
 after['open_issues'].append({'id':'RUNTIME_HOST_GZIP_HANDLING','status':'ACCEPTED LIMITATION','issue':'Explicit gzip alternatives are measured, not a CDN guarantee. Validate hosting byte serving and one-time decompression before client release. Older canonical checker has a closed recursive inventory; use runtime checker for the additive subtree.','artifact':'publication/sites/v1/runtime/CONTRACT.md'})
 return after
