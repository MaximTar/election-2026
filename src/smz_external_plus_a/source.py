"""Unchanged qualified source decoder and frozen real-adapter field mapping."""
import csv
import gzip
import json
from pathlib import Path
from src.smz_real_adapter import adapter as qualified
from src.smz_external_real.adapter import plans, PROFILE, FREEZE, sha
from .transport import require_active, RealRow, RealFrame, COUNTERS, IntegrityError

ROOT = Path(__file__).resolve().parents[2]


def load_primary():
    context = require_active()
    plan = plans()['primary']

    def provider(path, expected):
        require_active()
        if sha(ROOT/path) != expected:
            raise IntegrityError('SOURCE_SNAPSHOT_CHANGED')
        context['access_log'].append({'event':'REAL_COUNT_SOURCE_OPEN','path':path,'source':'primary'})
        return (ROOT/path).open('rb')

    frame = qualified._decode(plan,'primary',provider,run_id=context['run_id'],
        created_at=context['created_at'],bundle_sha=sha(PROFILE),
        origin='EXTERNAL_C_LITE_AUTHORIZED_REAL_SOURCE')
    qualified.verify_frame(frame)
    with gzip.open(FREEZE/'membership_metadata.csv.gz','rt',newline='') as f:
        metadata = {r['uuid']:r for r in csv.DictReader(f) if r['source']=='primary'}
    if set(metadata) != {r.uuid for r in frame.rows} or len(metadata)!=87736:
        raise IntegrityError('PRIMARY_MEMBERSHIP_CHANGED')
    output=[]
    for r in frame.rows:
        z=metadata[r.uuid]
        if (r.voters,r.issued,r.valid) != tuple(int(z[k]) for k in ['voters','issued','valid']):
            raise IntegrityError('FROZEN_METADATA_CHANGED')
        if r.known_invalid.status != z['invalid_status'] or (r.known_invalid.status=='DEFINED' and r.known_invalid.value!=int(z['known_invalid'])):
            raise IntegrityError('INVALID_MAPPING_CHANGED')
        statuses=(('ISTORIES','ELIGIBLE',''),('CEDAR','ELIGIBLE' if z['eligible_CEDAR']=='1' else 'EXCLUDED',z['cedar_exclusion_reason']))
        output.append(RealRow(r.uuid,z['official_region_id'],r.voters,r.issued,r.valid,r.parties[1],
            r.known_invalid.value if r.known_invalid.status=='DEFINED' else None,r.parties,
            r.source_variant,r.source_id,r.source_sha256,r.selector_commitment,r.tik_uuid,statuses))
    output.sort(key=lambda r:r.uuid)
    COUNTERS['real_party_rows'] += len(output)
    context['access_log'].append({'event':'REAL_ROWS_DECODED','source':'primary','count':len(output)})
    return RealFrame(tuple(output))
