"""Reconcile the existing stage-1.5 artifacts; never change data or universe membership.

--check validates the published state and Markdown against current artifacts without writing.
Default writes only the two handoff artifacts. Extend explicitly for subsequent stages.
"""
from src.analysis import descriptive_env  # noqa: F401
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

import pandas as pd

from src.data.schema import COUNTS, PARTIES

BASE = '20260923T110217085076Z'
VALIDATION = '20260923T112207Z_coverage_validation'
PROCESSED = Path('data/processed') / VALIDATION
TABLES = Path('outputs/tables') / VALIDATION
STATE = Path('outputs/metadata/research_state.json')
HANDOFF = Path('docs/RESEARCH_HANDOFF.md')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def metrics(frame):
    totals = {}
    for column in [*COUNTS, 'resolved_invalid']:
        values = pd.to_numeric(frame[column].replace('', pd.NA)).astype('Int64')
        missing = int(values.isna().sum())
        totals[PARTIES.get(column, column)] = {
            'sum_known': int(values.sum()), 'missing_rows': missing,
            'total': None if missing else int(values.sum()),
        }
    return {
        'rows': len(frame), 'regions': frame.resolved_region.nunique(),
        'region_names': sorted(frame.resolved_region.unique()),
        'region_code_missing_original': int(frame.region_code.eq('').sum()),
        'tik_proxy_count': len(frame[['resolved_region', 'tik']].drop_duplicates()),
        'counts': totals,
    }


def decision(id_, origin, decision_, rationale, impact, alternatives, consequences, stage='1.5'):
    return dict(id=id_, stage=stage, origin=origin, decision=decision_, rationale=rationale,
                quantitative_impact=impact, alternatives_considered=alternatives,
                reversibility='Raw и прежние universes сохранены; изменение требует нового именованного universe.',
                downstream_consequences=consequences)


def build(timestamp):
    data = read(PROCESSED / 'validated_union.csv.gz')
    assert data.uuid.is_unique
    main = data[data.record_origin.eq('main')]
    paper = main[main.voting_mode.eq('paper')]
    deg = main[main.voting_mode.eq('deg')]
    extra = data[data.record_origin.ne('main')]
    ready = data[data.analysis_ready_subset.eq('True')]
    excluded = paper[~paper.uuid.isin(ready.uuid)]
    assert (len(main), len(paper), len(deg), len(extra), len(ready), len(excluded)) == (87834,87737,97,373,70730,17007)
    assert set(ready.uuid) <= set(paper.uuid)
    persisted = read(PROCESSED / 'analysis_ready_paper_subset.csv.gz')
    assert ready.reset_index(drop=True).equals(persisted)
    raw = read(Path('data/raw') / BASE / 'uik_federal_parties.csv.gz')
    assert main[raw.columns].reset_index(drop=True).equals(raw)
    cov = read(TABLES / 'coverage_matrix.csv')
    frames = {
        'main_all_v1': main,
        'main_paper_v1': paper,
        'main_deg_v1': deg,
        'supplemental_added_v1': extra,
        'validated_union_v1': data,
        'paper_union_v1': data[data.voting_mode.eq('paper')],
        'paper_analysis_eligible_v1': ready,
        'main_paper_excluded_v1': excluded,
    }
    specs = {
        'main_all_v1': ('record_origin == "main"', 'Все supplemental UUID.', None, 'Архив всех исходных протоколов, без фильтра качества.'),
        'main_paper_v1': ('record_origin == "main" and voting_mode == "paper"', '97 строк DEG.', 'main_all_v1', 'Исходная бумажная рамка для reconciliation.'),
        'main_deg_v1': ('record_origin == "main" and voting_mode == "deg"', '87737 бумажных строк.', 'main_all_v1', 'Отдельная ветвь ДЭГ; семантика знаменателя не установлена.'),
        'supplemental_added_v1': ('record_origin != "main"', 'Все UUID, уже присутствующие в main.', None, '373 новых UUID; отдельно от альтернативных версий существующих строк.'),
        'validated_union_v1': ('True', 'Нет удалённых строк.', 'main_all_v1', 'Main + новые UUID, исходные counts не исправлены, evidence overlays отдельно.'),
        'paper_union_v1': ('voting_mode == "paper"', '97 строк DEG.', 'validated_union_v1', 'Бумажный union для coverage; не автоматически анализируемый набор.'),
        'paper_analysis_eligible_v1': ('analysis_ready_subset == "True"', 'Любое нарушение точного row/region predicate; voters <= 0 или valid <= 0.', 'main_paper_v1', 'Существующий строгий subset 1.5; не clean core и не национальная репрезентативная выборка.'),
        'main_paper_excluded_v1': ('record_origin == "main" and voting_mode == "paper" and analysis_ready_subset != "True"', 'Все включённые main paper UUID.', 'main_paper_v1', 'Диагностический complement для объяснения исключений; не новый аналитический запуск.'),
    }
    universes = []
    for name, frame in frames.items():
        inclusion, exclusion, previous, purpose = specs[name]
        selected = data if inclusion == 'True' else data.query(inclusion)
        assert set(selected.uuid) == set(frame.uuid), name
        old = frames[previous] if previous else frame.iloc[:0]
        removed = old[~old.uuid.isin(frame.uuid)]
        added = frame[~frame.uuid.isin(old.uuid)]
        key_changes = {}
        for label, columns in [('regions',['resolved_region']), ('tik_proxy',['resolved_region','tik'])]:
            before = set(map(tuple,old[columns].to_numpy()))
            after = set(map(tuple,frame[columns].to_numpy()))
            key_changes[label] = dict(input=len(before),removed=len(before-after),added=len(after-before),output=len(after))
            assert len(before)-len(before-after)+len(after-before)==len(after)
        universe = dict(name=name, snapshot=BASE, evidence_snapshot='validation_20260923T112207Z',
            artifact=str(PROCESSED/'validated_union.csv.gz'), inclusion=inclusion, exclusion=exclusion,
            purpose=purpose, previous_universe=previous, membership_sha256=hashlib.sha256(('\n'.join(sorted(frame.uuid))+'\n').encode()).hexdigest(),
            **metrics(frame), difference=dict(removed=metrics(removed), added=metrics(added),distinct_key_changes=key_changes))
        universes.append(universe)
    groups = {
        'incomplete_coverage': ['Ленинградская область','Республика Башкортостан'],
        'unresolved_denominator': ['Приморский край'],
        'counted_gt_issued': ['Архангельская область','Республика Марий Эл'],
        'conflicting_versions': ['Забайкальский край','Московская область','Республика Бурятия','Республика Мордовия','Республика Саха (Якутия)','Самарская область','Томская область','город Москва'],
    }
    grouped = {key: excluded[excluded.resolved_region.isin(names)] for key,names in groups.items()}
    assert sum(len(x) for x in grouped.values()) == len(excluded)
    assert len(set().union(*(set(x.uuid) for x in grouped.values()))) == len(excluded)
    partitions = [
        ('main_mode_split', main, {'paper':paper, 'deg':deg}),
        ('union_origins', data, {'main':main, 'supplemental_added':extra}),
        ('paper_selection', paper, {'included':ready, **grouped}),
        ('union_selection', data, {'included':ready, 'excluded_main_paper':excluded, 'deg':deg, 'supplemental_added':extra}),
    ]
    reconciliations = []
    for name, whole, parts in partitions:
        a = metrics(whole); b = {key:metrics(value) for key,value in parts.items()}
        assert set(whole.uuid) == set().union(*(set(x.uuid) for x in parts.values()))
        assert a['rows'] == sum(x['rows'] for x in b.values())
        for field, value in a['counts'].items():
            for statistic in ['sum_known', 'missing_rows']:
                assert value[statistic] == sum(x['counts'][field][statistic] for x in b.values())
        # Region and TIK keys can overlap across partitions: verify sets, never sum blindly.
        for cols in [['resolved_region'], ['resolved_region','tik']]:
            keys = lambda f: set(map(tuple, f[cols].to_numpy()))
            assert keys(whole) == set().union(*(keys(x) for x in parts.values()))
        reconciliations.append(dict(name=name, input=a, parts=b, verified=True,
                                    distinct_counts_note='Region/TIK verified by set union, not additive across overlapping parts.'))
    reasons = excluded.groupby('subset_exclusion_reasons').size().to_dict()
    ready_regions = set(ready.resolved_region)
    assert len(ready_regions)==72 and set(read(TABLES/'analysis_ready_regions.csv').region)==ready_regions
    omitted = cov[~cov.region.isin(ready_regions)].copy()
    omitted['excluded_observed_uiks'] = omitted.region.map(excluded.groupby('resolved_region').size()).fillna(0).astype(int)
    reason_map = {}
    for region in omitted.region:
        coverage = cov[cov.region.eq(region)].iloc[0]
        region_rows = data[data.voting_mode.eq('paper') & data.resolved_region.eq(region)]
        reasons_region = []
        if coverage.in_base_frame != 'True': reasons_region.append('outside_base_frame')
        if int(coverage.missing_uiks): reasons_region.append('missing_uiks='+coverage.missing_uiks)
        if coverage.denominator_status not in ['agreement','reconciled_by_explicit_Karelia_UUID']:
            reasons_region.append('denominator_status='+coverage.denominator_status)
        for flag,value,label in [('has_alternative','False','no_alternative'),('flag_counted_gt_issued','True','counted_gt_issued')]:
            count=int(region_rows[flag].eq(value).sum())
            if count: reasons_region.append(f'{label}={count}')
        count=int((region_rows.has_alternative.eq('True')&region_rows.alternative_matches.eq('False')).sum())
        if count: reasons_region.append(f'conflicting_versions={count}')
        count=int(region_rows.resolved_invalid.eq('').sum())
        if count: reasons_region.append(f'invalid_unknown={count}')
        reason_map[region]='; '.join(reasons_region)
    omitted['exact_exclusion_reason']=omitted.region.map(reason_map)
    assert int(excluded.row_integrity_ready.eq('True').sum())==15872
    original_issues = json.loads((TABLES/'issue_status.json').read_text())
    resolutions = {
        'leningrad_gap':'Получить 1019 отсутствующих UUID-протоколов из документированного источника.',
        'primorye_denominator':'Идентифицировать восемь UUID либо документировать исправление знаменателя.',
        'geographic_universe':'Явно определить национальную географическую рамку и получить её реестр.',
        'arithmetic_two':'Первичные версии двух протоколов и история исправлений.',
        'invalid_remaining':'Согласованный полный протокол для 188 записей; NULL не заменять на 0.',
        'deg_voters_semantics':'Первичная документация состава voters отдельно федерального и московского ДЭГ.',
        'district_missing':'Документированное соответствие UUID округу для 469 строк.',
        'source_versions':'Версии/время/первичные протоколы для 88 UUID, 208 полей.',
        'primary_access':'Получить первичные документы; зеркала с общим происхождением не независимы.',
    }
    issues=[]
    for item in original_issues:
        issues.append(dict(id=item['issue'],status=item['status'],description=item['decision'],affected=item['scope'],
            can_change_quantitative_results=item['issue'] not in ['ingestion_join','paper_field_mapping'],
            resolution_needed=resolutions.get(item['issue'],'Для текущего снимка evidence сохранён; пересмотреть при изменении источника.')))
    issues += [
        dict(id='region_gate_sensitivity',status='IMPORTANT',description='Codex choice: 1135 строк не прошли row integrity, но исключены 17007; ещё 15872 прошедших строки потеряны из-за регионального правила.',affected='Любой анализ 70730/72 и перенос выводов на страну.',can_change_quantitative_results=True,resolution_needed='Перед 2A явно выбрать подходящий цели universe; иной отбор оформить новым именем и сравнением, старый сохранить.'),
        dict(id='alternative_source_dependency',status='IMPORTANT',description='Каждая включённая строка требует альтернативного протокола одного зеркала; отсутствие evidence само блокирует регион.',affected='Состав strict subset, неопределённость происхождения.',can_change_quantitative_results=True,resolution_needed='Документировать зависимость и при необходимости проверить альтернативное правило в новом universe.'),
        dict(id='git_unavailable',status='ACCEPTED LIMITATION',description='git rev-parse HEAD не находит репозиторий; git_commit=null, commit не выдуман.',affected='Версионирование кода.',can_change_quantitative_results=False,resolution_needed='Создать доступный version-control checkout; до этого использовать SHA256 кода/артефактов.'),
    ]
    decisions = [
        decision('D01','user requirement','Только аудит; ДЭГ отдельно; не классифицировать аномалии и не оценивать контрфактические результаты.','Явная граница задания.','87834 = 87737 paper + 97 DEG.','Совместный анализ не разрешён.','Ни один universe не означает clean core.',stage='1 / 1.5'),
        decision('D02','researcher/Codex choice','Полное покрытие региона: missing UUID=0, outside registry=0.','Консервативный полный региональный набор; статистическая необходимость не установлена.','Отдельная непересекающаяся группа: исключены 3249 main paper строк двух регионов.','Построчный subset; разрешение частичного покрытия; анализ регионов с явной missingness.','Порог фактически 100%; даже один missing UUID исключает регион.'),
        decision('D03','researcher/Codex choice','Каждая бумажная строка региона должна пройти row_integrity_ready.','Строгая региональная сверка, выбранная Codex, а не требование пользователя.','Итог всех gates: 17007 строк/13 регионов; 1135 не прошли row integrity, 15872 прошли, но исключены. Конфликты версий исключают 11020 строк/8 регионов; 2 нарушения исключают 1262 строки/2 региона.','Изолировать проблемные UUID; раздельные universes для разных тестов.','Сильная чувствительность к единичной строке; не утверждать непригодность всех исключённых.'),
        decision('D04','researcher/Codex choice','Требовать альтернативный протокол и совпадение всех известных counts.','Проверка версии и целостности до анализа.','1045 main paper без альтернативы, все Башкортостан; 88 UUID имеют конфликты в 208 полях.','Не делать альтернативу обязательной; хранить confidence/evidence и анализировать отдельными слоями.','Зависимость отбора от доступности одного зеркала; совпадение не доказывает подлинность.'),
        decision('D05','researcher/Codex choice','Неразрешённый конфликт знаменателя блокирует регион; явный UUID Карелии допускает reconciliation.','Не объявлять меньший реестр полной страной.','Приморье: 1484 vs 1476, исключены 1476 строк; Карелия 472+1=473; 88806+1=88807.','Сохранить несколько frames и сделать sensitivity analysis по ним.','Нельзя скрывать восемь неизвестных комиссий сменой знаменателя.'),
        decision('D06','user requirement','Append-only supplemental snapshot, counts main неизменны, источник отдельным полем.','Не подменять основной снимок.','87834+373=88207; 41 новая строка исходной рамки имеет все counts=0; 332 зарубежных; восстановлено LEN=0.','Не добавлять строки и держать только evidence; альтернативные версии не заменяют main.','Union имеет другую географию; не использовать его молча как национальный dataset.'),
        decision('D07','user requirement','NULL не равен нулю без evidence; восстановление только отдельным overlay.','Не создавать вымышленные counts.','15329 исходных NULL = 15141 evidence zeros + 188 unknown; 15047 paper + 94 DEG восстановлений.','Оставить все NULL; иные источники с явным протоколом.','Сумма известных invalid не является полным total при missing>0.'),
        decision('D08','source constraint','Разделить семантику paper и DEG; issued/voters именовать issued_rate.','Paper mapping L1, L3+4+5, L9, L10; DEG population denominator не подтверждён.','97 DEG исключены из paper universe; все16 московских DEG имеют voters=issued.','Документировать корректный знаменатель из первичного источника.','Числовые суммы mixed voters ниже — bookkeeping, не уникальный electorate.'),
        decision('D09','researcher/Codex choice','Для rates subset требовать voters>0 и valid>0.','Неопределённые отношения не превращать в нули.','41 supplemental zero record не входит в strict subset; main paper дополнительно не исключён: 0.','Оставить нулевые строки в universe, задавать missing rates.','Zero records сохранены в coverage/union; coverage не равно число ненулевых протоколов.'),
        decision('D10','user requirement','Постоянный handoff, state JSON, reconciliation и self-review до финального ответа.','Передача исследования без потери существенных решений.','Текущая задача меняет данные/состав universe на 0 строк, 0 регионов и 0 голосов. Именованы восемь существующих представлений.','Только разрозненные отчёты не удовлетворяют требованию.','Новые stages обязаны расширять state, не перезаписывать старые universes.',stage='handoff setup'),
        decision('D11','researcher/Codex choice','Для учёта ТИК использовать proxy (resolved_region, tik), не выдумывать ID.','В CSV нет устойчивого уникального ID ТИК.','Точные proxy counts и set differences вычислены ниже; один ключ может встречаться в разных universes.','Получить официальный реестр IDs ТИК.','Особенно для DEG proxy не равен числу реальных территориальных комиссий.',stage='handoff setup'),
    ]
    inputs=[PROCESSED/'validated_union.csv.gz', PROCESSED/'analysis_ready_paper_subset.csv.gz', TABLES/'coverage_matrix.csv', TABLES/'analysis_ready_regions.csv', TABLES/'issue_status.json', Path('data/raw')/BASE/'uik_federal_parties.csv.gz']
    for dirname in [BASE,'20260923T112158513647Z','validation_20260923T112207Z']:
        manifest=Path('data/raw')/dirname/'manifest.json';inputs.append(manifest)
        for item in json.loads(manifest.read_text())['artifacts']:
            if 'sha256' in item: assert digest(manifest.parent/item['file'])==item['sha256']
    git=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True)
    state=dict(schema_version=1,active_snapshot_id=BASE,raw_sha256=digest(Path('data/raw')/BASE/'uik_federal_parties.csv.gz'),
        current_stage='handoff setup after 1.5; 2A not started',last_updated=timestamp,git_commit=git.stdout.strip() if git.returncode==0 else None,
        primary_analysis_universe='paper_analysis_eligible_v1',primary_universe_status='existing Codex-choice strict subset; purpose-specific suitability unresolved',
        primary_universe_definition={'code':'src/analysis/coverage_validation.py:222-230','region_all':['in_base_frame == True','missing_uiks == 0','observed_outside_registry == 0','denominator_status in [agreement, reconciled_by_explicit_Karelia_UUID]','all paper rows in region: row_integrity_ready == True'],'row_all':['row_integrity_ready == True','resolved_region in ready_regions','voters > 0','valid > 0'],'effective_coverage_threshold_pct':100,'threshold_origin':'researcher/Codex choice; statistical necessity not established'},
        available_analysis_universes=universes,row_counts={u['name']:u['rows'] for u in universes},region_counts={u['name']:u['regions'] for u in universes},
        metric_conventions={'regions':'Distinct resolved_region; original missing region count retained.','tik':'Distinct (resolved_region,tik) proxy, not a verified TIK ID.','voters':'Numeric source sum, not unique electorate; paper/DEG must not be treated as one denominator.','missing':'sum_known is partial; total=null if any field value unknown.'},
        methodological_decisions=decisions,open_issues=issues,
        open_blockers=[x['id'] for x in issues if x['status']=='BLOCKER'],open_important_issues=[x['id'] for x in issues if x['status']=='IMPORTANT'],
        reconciliations=reconciliations,excluded_regions=omitted.to_dict('records'),excluded_row_reason_combinations={k:int(v) for k,v in reasons.items()},
        input_sha256={str(p):digest(p) for p in inputs},code_sha256={str(p):digest(p) for p in sorted(Path('src').rglob('*.py'))},
        safe_to_proceed='YES WITH LIMITATIONS',proceed_scope='Only a separately requested stage on an explicitly chosen universe; no full-national inference or assumed clean core.',
        self_review={'large_prior_change':True,'fully_reconciled':True,'collateral_exclusions':True,'universe_membership_changed_this_task':False,'new_assumption':'TIK proxy explicitly defined; existing universes named without changing membership.','discretionary_decisions_disclosed':True,'source_dependency':True,'aggregate_contradictions':'Known source/protocol/denominator conflicts remain; bookkeeping identities pass.','reviewer_attention_required':True})
    return state


def table(headers, rows):
    escape=lambda x:str(x).replace('|',' / ').replace('\n',' ')
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(escape,r))+' |' for r in rows])


def render(s):
    lines=['# Research handoff / decision log',f"Обновлено: {s['last_updated']}. Этап: {s['current_stage']}.",
        '**Первым прочитать:** текущий primary — существующий строгий `paper_analysis_eligible_v1`, 70730 УИК / 72 региона. Это выбор Codex, не требование пользователя и не clean core. Из 17007 исключённых исходных бумажных строк 15872 сами прошли проверки. Полная страна не готова. Этап 2A не начат.',
        'Этот файл — живой handoff. Обновлять вместе с `outputs/metadata/research_state.json` в конце КАЖДОГО этапа до финального ответа. Новый состав требует нового имени universe и сравнения со старым. Исторические raw и universes не перезаписывать.',
        '### Provenance and stage history',
        f"Основной snapshot: `{s['active_snapshot_id']}`; main SHA256 `{s['raw_sha256']}`. Повторный snapshot `20260923T112158513647Z` имеет те же распакованные CSV. Evidence: `validation_20260923T112207Z`, 215 HTTP-попыток, 90 реестров и 90 федеральных региональных JSON; manifest содержит URLs, UTC timestamps и SHA256. Supplemental не независим от автора: общие provenance-источники. Первичные порталы не удалось получить.",
        'Этап 1: сохранён основной массив и DATA AUDIT. Этап 1.5: coverage/source/semantics validation, overlays, supplemental, строгий subset. Последующий derivation review: раскрыта потеря целых регионов. Текущий этап: только handoff и проверки, без изменения состава данных.',
        f"Git commit: `{s['git_commit']}` (репозиторий недоступен для rev-parse; commit не выдуман). SHA256 входов и кода сохранены в JSON.",
        '### Analysis universes',
        'Имена ниже закрепляют уже существующие представления, не создают новый фильтр. Все выбираются из `data/processed/20260923T112207Z_coverage_validation/validated_union.csv.gz`. Snapshot каждого: основной `20260923T110217085076Z` + evidence `validation_20260923T112207Z`. Regions считаются по resolved_region; одна исходная строка без кода отнесена к Карелии с evidence. ТИК — proxy (resolved_region,tik), для ДЭГ не число физических ТИК. Суммы voters смешанных режимов — только бухгалтерское сложение полей, не уникальный electorate.',
        table(['Universe','Rows','Regions','TIK proxy','voters sum','issued','valid'],[[u['name'],u['rows'],u['regions'],u['tik_proxy_count'],u['counts']['voters']['sum_known'],u['counts']['issued']['sum_known'],u['counts']['valid']['sum_known']] for u in s['available_analysis_universes']])]
    for u in s['available_analysis_universes']:
        delta=u['difference'];lines.append(f"**{u['name']}**. Inclusion: `{u['inclusion']}`. Exclusion: {u['exclusion']} Цель: {u['purpose']} Предыдущий: `{u['previous_universe']}`; удалено {delta['removed']['rows']}, добавлено {delta['added']['rows']}. Точные removed/added totals всех партий, denominator и missingness хранятся в JSON; membership SHA256: `{u['membership_sha256']}`.")
    lines += ['Точный gate строгого subset: регион в исходной положительной рамке; missing_uiks=0; observed_outside_registry=0; denominator_status ∈ {agreement, reconciled_by_explicit_Karelia_UUID}; ALL бумажные строки региона проходят row_integrity_ready. Строка дополнительно требует voters>0 и valid>0. Одна не прошедшая строка исключает регион целиком. Coverage gate = ровно 100%, не эмпирически обоснованный оптимум.',
        'row_integrity_ready = paper AND alternative_matches AND resolved_invalid known AND voters>=0 AND issued<=voters AND no negative original counts AND valid+resolved_invalid<=issued AND party sum=valid AND L7+L8=L9+L10 AND L2+L12=L3+L4+L5+L6+L11 AND resolved_region known. alternative_matches требует альтернативный протокол и совпадение всех известных main counts. NULL сравнения пропускаются, NULL не равен 0. Точный исполняемый predicate: src/analysis/coverage_validation.py:222–230. Пустой district не является отдельным фильтром.',
        '### Arithmetic reconciliation',
        'Все следующие равенства проверены программно по UUID и целым counts. Missingness тоже складывается; известные суммы invalid не выдаются за полный total. Distinct region/TIK counts проверяются через множества, поскольку они могут пересекаться между частями.',
        '87834 = 87737 paper + 97 DEG. 88207 = 87834 main + 373 supplemental. 373 = 41 zero-count records исходной рамки + 332 зарубежных. 87737 = 70730 + 17007; 85 = 72 + 13 регионов. Все 70730 — main paper. 88207 = 70730 + 17007 + 97 + 373. В этом этапе изменений членства/голосов: 0.',
        'Missing invalid: 15329 = 15141 evidence-recovered zeros + 188 unknown; 15141 = 15047 paper + 94 DEG. Raw NULL сохранены. 188 = 170 без альтернативы + 18 конфликтующих. 469 district NULL не восстановлены.',
        'Coverage: 87737 + 41 = 87778 paper UUID исходной рамки; 88799 - 87778 = 1021 = 1019 LEN + 2 Башкортостан. Дополнительно 8 комиссий Приморья относительно author denominator не идентифицированы. 88806+1 Карелия=88807; 88807-8=88799. Расширенный реестр 91381 = 88799+333 зарубежных+2249 четырёх территорий. Эти рамки не взаимозаменяемы.']
    for r in s['reconciliations']:
        fields=['voters','issued','valid','invalid','resolved_invalid',*PARTIES.values()]
        lines.append(f"**{r['name']}** — input = сумма частей; значения ниже — `sum_known` (для invalid при NULL частичные).")
        lines.append(table(['metric','input',*r['parts']],[[f,r['input']['counts'][f]['sum_known'],*[v['counts'][f]['sum_known'] for v in r['parts'].values()]] for f in fields]))
        lines.append(table(['part','rows','regions','TIK proxy','invalid missing','resolved_invalid missing'],[[key,v['rows'],v['regions'],v['tik_proxy_count'],v['counts']['invalid']['missing_rows'],v['counts']['resolved_invalid']['missing_rows']] for key,v in r['parts'].items()]))
    lines.append('Изменения числа регионов/ТИК относительно предыдущего universe: A - removed_keys + added_keys = B; ключи считаются distinct, не суммой строк.')
    us={u['name']:u for u in s['available_analysis_universes']}
    # TIK keys for exact set-difference reporting.
    data=read(PROCESSED/'validated_union.csv.gz')
    for u in us.values():
        if not u['previous_universe']:continue
        old=us[u['previous_universe']]
        select=lambda expression: data if expression=='True' else data.query(expression)
        a=select(old['inclusion']);b=select(u['inclusion'])
        for label,cols in [('regions',['resolved_region']),('TIK proxy',['resolved_region','tik'])]:
            keys=lambda f:set(map(tuple,f[cols].to_numpy()))
            aa,bb=keys(a),keys(b)
            lines.append(f"- {u['previous_universe']} → {u['name']}, {label}: {len(aa)} - {len(aa-bb)} + {len(bb-aa)} = {len(bb)}.")
    lines += ['### Excluded regions',
        'expected/observed/missing относятся к реестру зеркала и union; excluded_observed — только main paper. Москва observed=1443, main excluded=1442: одна supplemental zero row. Причины регионального исключения и их количественный эффект раскрыты в D02–D05 и комбинациях ниже.',
        table(['region','expected','observed','missing','coverage %','main excluded','exact exclusion reason'],[[r[k] for k in ['region','expected_uiks','observed_paper_uiks','missing_uiks','coverage_pct','excluded_observed_uiks','exact_exclusion_reason']] for r in s['excluded_regions']]),
        table(['Exact row reason combination','main rows'],s['excluded_row_reason_combinations'].items()),
        'Региональные группы без двойного счёта: coverage 3249 + denominator 1476 + counted_gt_issued 1262 + conflicting_versions 11020 = 17007. У Башкортостана есть дополнительные причины, но в этой сумме он учтён только в coverage.',
        '### Methodological decisions']
    for d in s['methodological_decisions']:
        lines.append(f"**{d['id']} · этап {d['stage']} · {d['origin']}**\n\nРешение: {d['decision']}\n\nRationale: {d['rationale']}\n\nQuantitative impact: {d['quantitative_impact']}\n\nAlternatives considered: {d['alternatives_considered']}\n\nReversibility: {d['reversibility']}\n\nDownstream consequences: {d['downstream_consequences']}")
    lines.append('### Open issues')
    for i in s['open_issues']:
        lines.append(f"**{i['id']} — {i['status']}**. {i['description']} Затрагивает: {i['affected']} Может изменить количественный результат: {'да' if i['can_change_quantitative_results'] else 'нет'}. Для разрешения: {i['resolution_needed']}")
    lines += ['### Self-review',
        '- Крупная историческая разница: да, 17007/13; арифметика полностью объяснена выше для rows, regions, TIK proxy, voters, issued, valid и каждой партии.\n- Исключены прошедшие строки: да, 15872 из-за регионального gate.\n- В этой задаче membership не изменён; новые имена лишь фиксируют имеющиеся представления.\n- Новое определение учёта: ТИК proxy, не официальный ID; D11.\n- Субъективные choices: да, полное покрытие, all-rows gate, обязательная альтернатива, региональный denominator gate, положительные знаменатели. Это Codex choices, rationale и альтернативы явно записаны.\n- Зависимость от источника/параметра: да, зеркало и all-rows/100% gate.\n- Противоречия: bookkeeping identities проходят; первичные конфликты counts и знаменателей остаются.\n- Reviewer должен увидеть это до 2A; ограниченный набор не подтверждает применимость модели.',
        '### Reproduction and verification',
        'Проверка без записи: `python3 -m src.analysis.research_handoff --check`. Обновление только текущего handoff/state: `python3 -m src.analysis.research_handoff`. Проверяются raw SHA256, точная неизменность main, готовый subset, UUID partitions, суммы и missingness всех counts, множества регионов/ТИК. Для нового этапа расширить builder/решения/universes; не перегенерировать старое описание как будто это новый этап. Общие sanity tests: `python3 -m unittest discover -s tests -v`.',
        'Подробные evidence: outputs/reports/20260923T112207Z_coverage_validation.md; outputs/tables/20260923T112207Z_coverage_validation/{coverage_matrix.csv,source_conflicts.csv,arithmetic_evidence.csv,subset_membership.csv.gz}. История этапа 1 сохранена отдельно. JSON содержит полные absolute totals, missing counts, отличия universes и hashes.',
        '### Reviewer attention',
        '**Этап 1:** 87834 строки, 15329 invalid NULL, 469 district NULL, 1 region code NULL, 2 превышения counted над issued; ДЭГ нельзя смешивать с бумажным знаменателем. Архивные turnout-имена не означают подтверждённую явку.',
        '**Этап 1.5:** 17007 наблюдаемых paper строк исключены через 13 целых регионов; 15872 из них прошли row integrity. Это существенный Codex choice. LEN 1/1020, recovery=0. Приморье 1484 vs1476; 88 конфликтующих UUID/208 fields; 188 invalid unknown; 1045 paper без альтернативы. Mirrors имеют общее происхождение. 41 zero record улучшает record coverage, не добавляя голосов. Foreign records меняют geography. 97 DEG исключены из paper. Ни один факт не доказывает аномалию или чистоту ядра.',
        '**Derivation review:** правило all-rows/full-region впервые явно количественно раскрыто; оно может менять будущие результаты сильнее, чем локальные дефекты. Перед следующим анализом требуется явный выбор universe по цели задания.',
        '**Handoff setup:** ни один протокол/count/membership не изменён. Восемь существующих представлений получили постоянные имена; введён явно ограниченный ТИК proxy. Git commit отсутствует; hashes сохранены. JSON и Markdown сверяются отдельной read-only командой.',
        '**Safe to proceed: YES WITH LIMITATIONS** — только по отдельному заданию на явно выбранном universe. Полный national analysis, совместный paper/DEG rate и признание clean core не разрешены этими проверками.']
    return '\n\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=12:
        from src.stage3a.governance import check
        check()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=11:
        from src.data.identity_validation_evidence import check
        check()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=10:
        from src.data.identity_validation_design import check
        check()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=9:
        from src.analysis.precinct_enrichment_report import verify
        verify()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=8:
        from src.analysis.forensics_2b2_report import verify
        verify()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=7:
        from src.analysis.temporal_schedule_report import verify
        verify()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=6:
        from src.analysis.temporal_verify import verify
        verify()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=5:
        from src.analysis.forensics_2b1_verify import verify
        verify()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=4:
        from src.analysis.forensic_common import Store
        from src.analysis.forensic_report import verify, publish
        store=Store()
        verify(store)
        if not args.check:
            publish(store)
            store.manifest()
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=3:
        from src.analysis.descriptive import verify, ROOT
        verify(ROOT)
        if not args.check:
            from src.analysis.descriptive_report import publish
            publish(ROOT)
        return
    if STATE.exists() and json.loads(STATE.read_text()).get('schema_version',1)>=2:
        from src.analysis.universes import main as current_stage
        current_stage(['--check'] if args.check else ['--write'])
        return
    old=json.loads(STATE.read_text()) if args.check else None
    timestamp=old['last_updated'] if old else datetime.now(timezone.utc).isoformat()
    state=build(timestamp);markdown=render(state)
    if args.check:
        assert state==old, 'research_state.json is stale or changed; review before updating.'
        assert HANDOFF.read_text()==markdown, 'RESEARCH_HANDOFF.md does not match reviewed state.'
        print('PASS: raw hashes, membership, four partitions, all count totals/missingness, region/TIK sets, JSON and Markdown.')
    else:
        STATE.parent.mkdir(parents=True,exist_ok=True)
        STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
        HANDOFF.write_text(markdown)
        print(f'Written {HANDOFF} and {STATE}; data and universe membership unchanged.')


if __name__=='__main__':
    main()
