# English translation v1: decisions and integration contract

## Authority and scope

This is a translation layer over Russian release `ru-release-v1`, commit `20bacb4c343e952062599889ea4a4938fb258b98`. Russian remains authoritative. No calculation, scientific state, source version, default, applicability rule or result is changed. English artifacts are not a new scientific release and do not create an `en-release-v1` tag.

The complete technical and narrative sources are translated separately. The shorter narrative is not expanded into a technical paper. First-person research history, the author's decisions and reader-inclusive language are retained. All source links remain unchanged, including Russian-language destinations.

## Terminology

- UIK and TIK are retained. The first relevant occurrence expands to precinct election commission (UIK) and territorial election commission (TIK). English plurals are UIKs and TIKs. No data identifier is renamed.
- The ten canonical party labels and stable party IDs are listed in `glossary.md` and `site_strings.json` under `party.*`. They are consistent short display names, not claims about a full English legal name. The longer site label for `sr` and the shorter article label map to A Just Russia. Rodina is not alternated with Motherland.
- Important Stories and Novaya Gazeta Europe are the English reader names. Existing `vazhnye_istorii`, `istories`, `novaya_1d`, `novaya_2d` and other machine IDs remain unchanged. The source attribution is Zhizhin, without inventing a given name from incomplete metadata.
- “Honest core” stays quoted and attributed to the external authors. A visual core and a selected fitted component remain distinct. “Comet tail” is descriptive visual language, not a new statistical definition.
- Cedar returns a signed model residual relative to observed focal-party votes. “Residual” never becomes ordinary party share or a proven fraudulent-vote count.
- Model support, supported target precincts and applicability describe where the prescribed calculation is defined. Political support is called voter support only where the Russian source actually uses that meaning.
- The Important Stories control is a reference window. Reference range is the ordinary-prose equivalent. Cedar's single reference bin is a reference interval. Neither sensitivity range is a confidence interval.
- Ballots issued / registered voters is preserved as the project participation coordinate. Cedar's coordinate remains (valid + known invalid ballots) / registered voters.
- The frozen symbolic decomposition retains `Qисх`, `Kсостав`, `Kобъём` and `Kвзаимодействие` exactly. These are formula identifiers, not untranslated prose. Respectively, they denote the original quantity, composition term, volume term and interaction term. Inline coordinate descriptions are translated, but the mathematical operations are unchanged.
- In the narrative Cedar example, “первый показатель” is rendered “the residual measure” to preserve the explicitly stated referent after the two illustrative percentages. No number, denominator or conclusion is changed.
- Thousands-grouping spaces, decimal points and all numerical precision are retained. Compact labels use `pp`. The few decimal commas in existing UI control labels become decimal points without changing their values.

## Translation and research disclosures

Every future English reader-facing route must show this exact notice:

> Machine-translated from Russian with OpenAI models. The Russian release is the authoritative version.

The associated link label is `Russian version`. Both translated articles also contain the required longer **Translation note.** immediately after their title/subtitle area. This is new translation-provenance copy and must not be backported to Russian. The separate, existing research-AI disclosure is translated in full and retains the human author's responsibility for what and how to calculate and which variants to test.

## Catalog coverage and source priority

`site_strings.json` is a flat semantic-key → English-string catalog. It excludes article bodies. It covers navigation, page shells, baseline and Explorer controls, all ten parties, 84 existing region UUIDs, 16 existing A/B/C designs, five D labels, four source versions, method cards, chart axes/legends/captions/tooltips, applicability, errors/loading states, licensing, reproducibility and footer text.

`site_copy_inventory.json` records captured public reader-bundle hashes, literal-to-key mappings, frozen repository sources and route-shell captures. Russian strings there are intentional source evidence, not fallback reader copy. Nested JavaScript templates were inspected separately: complete messages use named presentation placeholders such as `{previous}`, `{current}` and `{region}`. They are not executable JavaScript. Adjacent fragment keys are retained for traceability, but new integration should prefer the complete message. Region names are display aliases for the frozen registry labels, not changes to geography, membership or political status.

One source conflict was resolved by the requested priority order. The captured live Sources UI still says that reproduction materials have not yet been fully released. The higher-priority frozen Russian article and `reproducibility-v1` documents establish that the materials are already public. `sources.reproducibility_status` translates that current authoritative statement and explicitly retains the non-redistributed raw-snapshot limitation. The stale UI sentence is recorded in the inventory but is not carried into English. No Russian site or source file was edited.

Supplementary complete tooltip/caption templates express meanings already present in the frozen article/data contract. They add no calculation or scientific interpretation. License copy preserves the eligible-project-authorship boundary and third-party exclusions, including mixed-origin Cedar code. Raw snapshots are not republished by project policy, not declared legally forbidden to redistribute.

## Future routes and locale switching

| Russian route | English route |
|---|---|
| `/` | `/en/` |
| `/article` | `/en/article` |
| `/methods` | `/en/methods` |
| `/sources` | `/en/sources` |

Switch only the presentation locale. Preserve the current page, query parameters, scientific `state` ID and selected frozen configuration. English uses the same availability lists, source versions, methods, numbers and exact resources. Never create English scientific-state duplicates or a Cartesian product of controls. CARD_ONLY methods remain state-less. INTERNAL states remain unavailable to the reader.

Article heading fragments may need a RU↔EN heading map during Sites integration because translated headings have different text. Do not alter the frozen Markdown to implement that map. The source links inside the articles remain verbatim and are not silently retargeted to English routes.

Translate labels at rendering boundaries by stable IDs. Do not change publication JSON keys, identifiers, formulas, stored numeric values or data files. Preserve missing/undefined semantics. Use prepared display values and a decimal-point locale. Do not coerce exact large-integer strings to JavaScript Number. No client-side scientific arithmetic or new fit is needed.

This task supplies translation artifacts only. The English routes have not been implemented, and no English browser/layout QA is claimed.

## Figure anchors

All eight anchors stay on the same source-line positions after removing the two added translation-note lines. They remain editorial instructions, not reader-facing paragraphs. The table below records every mapping in source order.

| RU source line | Russian anchor | English anchor |
|---:|---|---|
| 45 | Место для графика: исходные результаты и основные A/B/C для всех десяти партий | Figure placeholder: observed results and default A/B/C for all ten parties |
| 94 | Место для графика: исходное распределение голосов между десятью партиями | Figure placeholder: observed distribution of votes among the ten parties |
| 313 | Место для графика: двумерная плотность УИК основной базы — по горизонтали отношение выданных бюллетеней к зарегистрированным избирателям, по вертикали доля фокальной партии среди действительных голосов | Figure placeholder: two-dimensional density of UIKs in the primary dataset — horizontal axis: ballots issued / registered voters, vertical axis: focal-party share of valid votes |
| 487 | Место для графика: исходные результаты и A/B/C — изменение по всем десяти партиям | Figure placeholder: observed results and A/B/C — changes for all ten parties |
| 597 | Место для графика: наблюдаемая и ожидаемая кривые Cedar с выбранным опорным интервалом 43–44% | Figure placeholder: Cedar observed and expected curves with the selected 43–44% reference interval |
| 629 | Место для графика: результат Cedar при разных опорных интервалах, с числом УИК и объёмом голосов в каждом интервале | Figure placeholder: Cedar result at different reference intervals, with UIK counts and vote volumes in each interval |
| 663 | Место для графика: наблюдаемые голоса фокальной партии и остальных по уровню участия, ожидаемая кривая проектной реконструкции и выделенный опорный диапазон 20–30% | Figure placeholder: observed votes for the focal party and the others by participation level, the expected curve of the project reconstruction, and the highlighted 20–30% reference range |
| 948 | Место для графика: несколько панелей чувствительности — A/B/C, D, опорные диапазоны «Важных историй», опорные интервалы Cedar, 1D и 2D | Figure placeholder: several sensitivity panels — A/B/C, D, Important Stories reference ranges, Cedar reference intervals, 1D and 2D |

## Validation and limits

Run `python3 -B publication/i18n/en/v1/validate_translation.py` from the repository. The read-only checker verifies source bindings, every numeric token and table-cell placement, URL sequence, full line/block structure, formulas, emphasis, all figure anchors, catalog mappings and package hashes. It does not run scientific code.

The separate semantic pass compares the translations against Russian after drafting, including negation, attribution, denominators, uncertainty, source fidelity and the bounded anomaly-aware NO-GO. Its section coverage and outcomes are in `semantic_review.json`. It was performed by the same OpenAI assistant in a separate pass, not by an independent human reviewer. Mechanical checks do not prove semantic equivalence by themselves. Translation errors remain possible, as disclosed.
