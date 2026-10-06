"""Single source of numerical specifications; frozen by manifest, never tuned."""
from pathlib import Path
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
# WSL workspace permissions name the lower-case mount alias. Use it only when it
# is demonstrably the same directory; scientific paths stay repository-relative.
_alias = Path('/mnt/c/users/max_1/pycharmprojects/election-2026')
if _alias.exists() and _alias.samefile(ROOT):
    ROOT = _alias
OUT = ROOT / 'outputs/stage3a/freeze'
SNAP = '20260923T110217085076Z'
DESIGN_SOURCE = 'data/processed/universe_revision_v2/paper_primary.csv.gz'
HIERARCHY_SOURCE = 'data/external/cik_temporal_2026/data/processed/commission_hierarchy.csv.gz'
CONFIG = {
    'version': '3A-v1', 'seed_namespace': 'stage3a-prospective-20260927-v1',
    'snapshot': SNAP, 'primary_universe': 'paper_primary', 'parties': 10,
    'party_order': ['rodina','er','kprf','pensioners','new_people','direct_democracy',
                    'greens','communists_russia','ldpr','sr'],
    'future_real_seed_key': ['real-release', SNAP, '<exact_registered_universe_name>'],
    'actual_design': {'rows': 87734, 'regions': 84, 'tiks': 2818, 'voters': 99359922},
    'predictors': ['H_count_ridge', 'L_peer_mixture'],
    'prediction_tasks': ['known_tik', 'heldout_tik'], 'folds': 5,
    'H': {'precision': [80., 200., 60.], 'prior_sd': [10., 1.5, .75, .75],
          'maxiter': 1000, 'maxls': 40, 'gtol': 1e-6, 'ftol': 1e-12,
          'gradient_acceptance': 1e-4, 'logit_bound': 15.},
    'L': {'min_pool': 8, 'k': 32, 'min_bandwidth': float(np.log(1.10)),
          'pseudocount': .5},
    'association': {'name': 'A_exact_size_categorical_projection',
          'min_tiks': 40, 'min_regions': 20, 'min_rows': 2000,
          'min_fraction': .02, 'caliper': 0, 'min_pairs_per_tik': 1,
          'alpha': .05, 'B': 1999, 'projection_draws': 1, 'primary_correction': 'Holm',
          'null_cdf_points': [.01, .05, .10],
          'null_cdf_upper_limits': [.025, .075, .13]},
    'R_null': 5000, 'R_positive_per_strength_sign': 1000,
    'positive_strengths': [.10, .30, .60], 'positive_signs': [-1, 1],
    'positive_definition': 'logit loading, not correlation',
    'scenarios': [f'N{i}' for i in range(1, 11)],
    'association_nulls': [f'N{i}' for i in range(1, 9)],
    'predictive_draws': 1999, 'nominal_coverage': .95,
    'gate': {'simultaneous_error': .05, 'coverage_floor': .92,
             'fit_success_floor': .99, 'association_fwer_ceiling': .075,
             'pit_points': [.01, .05, .10, .50, .90], 'pit_margin': .05,
             'support_fraction': 1., 'min_regions': 20, 'min_tiks': 40,
             'numeric_rtol': 1e-10, 'numeric_atol': 1e-12},
    'strata': ['all', 'size_q0', 'size_q1', 'size_q2', 'size_q3',
               'tik_n_lt10', 'tik_n_10_29', 'tik_n_ge30'],
    'statuses': {'shpilkin': 'D_DROP', 'KYHT': 'D_DROP',
                 'robust_smooth_standalone': 'DROP', 'history': 'EXCLUDED'},
    'real_execution': False, 'sequential_extension': False,
    'sensitivity': ['no_source_conflicts', 'alt_conflict_versions', 'complete_regions',
                    'coverage_95', 'coverage_99p9', 'leave_one_region_out'],
    'parameter_sensitivity': 'NONE; new priors/bandwidth/support rules need a new version',
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def seed(*parts):
    payload = json.dumps([CONFIG['seed_namespace'], *parts], separators=(',', ':'), ensure_ascii=False)
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:16], 'big')


def rng(*parts):
    return np.random.Generator(np.random.PCG64(seed(*parts)))


def write_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def frozen():
    manifest = json.loads((OUT/'manifest.json').read_text())
    for p, h in manifest['files'].items():
        if digest(ROOT/p) != h:
            raise RuntimeError('Frozen artifact changed: ' + p)
    for p, h in manifest['inputs'].items():
        if digest(ROOT/p) != h:
            raise RuntimeError('Frozen input changed: ' + p)
    if json.loads((OUT/'config.json').read_text()) != CONFIG:
        raise RuntimeError('Config/code mismatch')
    return manifest
