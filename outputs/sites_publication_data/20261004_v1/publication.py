import copy,json
from pathlib import Path
P=Path(__file__).resolve().parent
def build_state(before):
 d=json.loads((P/'decision.json').read_text());assert before['current_stage']==d['predecessor']
 after=copy.deepcopy(before)
 after.update(current_stage=d['publication_id'],last_updated=d['published_at'],safe_to_proceed='YES WITH LIMITATIONS',proceed_scope=d['scope'])
 after[d['state_field']]=d
 after['methodological_decisions'].extend(json.loads((P/'decision_ledger.json').read_text())['decisions'])
 after['open_issues'].append({'id':'SITES_PUBLICATION_EDITORIAL_PENDING','status':'ACCEPTED LIMITATION','issue':'Final reader copy, license/release metadata and future UI review remain separate; no scientific blocker. Large exact sidecars are lazy.','artifact':'publication/sites/v1/CONTRACT.md'})
 return after
