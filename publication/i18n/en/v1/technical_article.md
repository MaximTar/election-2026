# Same Data, Different Models

*How the answer changes when different calculation rules are applied to the same data*

**Translation note.** This English version was translated from the original Russian with OpenAI models and checked for semantic consistency. The Russian release remains the authoritative version. Translation errors are still possible.

I came across [an article by Novaya Gazeta Europe](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty),
which estimated United Russia's result in paper voting at around 34%, and wondered: **how exactly did they arrive at that number?**

As I looked into it, it became increasingly clear that there was no single formula.
You have to decide which precincts to compare, which part of the data to use as a reference, which values to recalculate, which to leave as reported, and what to do where no comparison can be constructed.

So the question became broader: **what happens if we apply several different calculation methods to the same data?**

Below, I will call these calculations **scenarios**. One point needs to be clear from the start: a scenario does not recover the “true” election result.
It answers a narrower question: **what happens if we accept a particular set of rules and apply it consistently to the data?**

Another point needs to be made straight away: **the aim is not to decide which authors of published estimates are “right”, or to compare methods as candidates for the one correct percentage**.
Scenarios can answer different questions, so two results expressed as percentages cannot automatically be read as two estimates of the same thing.
The converse matters too: **this research does not defend the official result or claim that there were no violations or fraud**.
It seeks to answer a narrower question: what exactly do different statistical rules produce?
What interests me more is the assumptions behind each number and how much the result changes when those assumptions change.

TL;DR: **the result depends not only on the data, but also on the question we ask of them.**
A percentage by itself explains little until we know exactly what was calculated and what it was compared with.

## First, an example

By a scenario family, I mean several calculation variants built around the same basic idea.

In the first such family, the rules changed values only for precincts for which the model's prescribed comparison group could be found.
We will look at scenarios A, B and C in detail below. For now, it is enough to know that they change the distribution of votes and the overall scale of counts in different ways.

| Party | Observed | A | B | C |
|---|---:|---:|---:|---:|
| Rodina | 0.65% | 0.66% | 0.65% | 0.65% |
| United Russia | 58.74% | 58.35% | 58.76% | 58.51% |
| Communist Party of the Russian Federation | 14.59% | 14.76% | 14.60% | 14.71% |
| Pensioners' Party | 1.91% | 1.94% | 1.91% | 1.93% |
| New People | 7.60% | 7.68% | 7.59% | 7.64% |
| Party of Direct Democracy | 0.35% | 0.35% | 0.35% | 0.35% |
| Greens | 0.96% | 0.97% | 0.95% | 0.96% |
| Communists of Russia | 0.80% | 0.81% | 0.80% | 0.81% |
| Liberal Democratic Party of Russia | 9.30% | 9.35% | 9.29% | 9.33% |
| A Just Russia | 5.11% | 5.13% | 5.10% | 5.11% |

Figure placeholder: observed results and default A/B/C for all ten parties

Across the full dataset, these three scenarios change the picture fairly modestly. But this is only one family of calculations.
In other words, **this is not a summary of the whole study, just a simple first example**.

Later, you will see methods that work quite differently: some compare one selected party with all the others combined, while others try to find a characteristic area (a “core”) within the distribution of results itself.
Some of the percentages that follow therefore cannot be placed alongside the table above and read as four more versions of the same result.

Before looking at those differences, though, let us examine the data and the basic rules: which precincts are compared, what exactly is recalculated, and which part of the data the model can work on at all.

## Which data are included in the study?

The primary dataset contains 87 736 precinct election commission (UIK) records from 84 regions, 99 360 758 registered voters and 54 723 201 valid votes.
These are paper-voting data: remote electronic voting (DEG) and overseas precincts are stored separately and are not mixed into this dataset.

The main source of party results is a saved export from `deg.zhizhin.xyz`, compiled from official protocols.
Its provenance is also described in [the dataset entry on Electoral.Graphics](https://www.electoral.graphics/ru-ru/%D0%92%D1%8B%D0%B1%D0%BE%D1%80%D1%8B-%D0%B8-%D0%94%D0%B0%D0%BD%D0%BD%D1%8B%D0%B5/%D1%80%D0%BE%D1%81%D1%81%D0%B8%D1%8F-%D0%BF%D0%B0%D1%80%D0%BB%D0%B0%D0%BC%D0%B5%D0%BD%D1%82-2026-5).
The [public Neshodilina API](https://neshodilina.netlify.app/api) was also used to check discrepancies.
Separate material from the Central Election Commission (CIK) and election commissions was used for the commission hierarchy, temporal checks and later verification of disputed records.

The calculation is tied to a particular saved version of the data because the official source can change over time.
Later CIK values were used to check discrepancies, not to retrospectively change calculations whose results had already been revealed.

<details>
<summary>Why save a separate copy of the data when the CIK exists?</summary>

To repeat a calculation, you need to know exactly which state of the data it used.
If the official source later updates individual values, that is useful new information, but it should not silently change a completed calculation.

Later official protocols were therefore used to check the provenance of discrepancies.
If we want to calculate a result using a newer state of the data, it should be a separate, explicitly identified variant, not a retrospective replacement of the old one.

</details>

In the primary version, valid votes are distributed among the ten parties as follows:

| Party | Votes | Share of valid votes |
|---|---:|---:|
| Rodina | 355 312 | 0.65% |
| United Russia | 32 143 992 | 58.74% |
| Communist Party of the Russian Federation | 7 983 282 | 14.59% |
| Pensioners' Party | 1 044 022 | 1.91% |
| New People | 4 159 960 | 7.60% |
| Party of Direct Democracy | 190 862 | 0.35% |
| Greens | 523 717 | 0.96% |
| Communists of Russia | 438 044 | 0.80% |
| Liberal Democratic Party of Russia | 5 086 868 | 9.30% |
| A Just Russia | 2 797 142 | 5.11% |

Figure placeholder: observed distribution of votes among the ten parties

<details>
<summary>What exactly was left out of the primary dataset, and why?</summary>

The primary dataset had been assembled by 27 September 2026.

The largest gap is Leningrad Oblast. Its registry contains 1 020 UIKs, but usable final party results had been found for only one of them in the data collected by that point.
Under a predefined rule, an entire region was excluded if coverage by final party data was below 99%.
That single available row was therefore not inserted into the overall dataset as though it represented the whole region.

Within the other 84 regions, a further 43 records were excluded.
For 41, the number of registered voters and the number of valid votes could not both be obtained, so the rows did not allow an ordinary party result to be calculated correctly.
In another two, the sum of known valid and invalid ballots exceeded the number of ballots issued.

The project registry separately includes the DPR, LPR, Zaporizhzhia and Kherson regions (2 249 UIKs in total), but the collected dataset contains no final party results for them.
They were not filled in with zeros or treated as part of the primary dataset.

DEG is stored separately because the study's primary dataset consists of precinct-level paper-voting protocols.
Overseas UIKs are also kept separate: data for 332 overseas precincts out of 333 in the registry are stored separately.

By UIK count, the primary dataset covers 87 736 of the 87 779 precincts in the included 84 regions, or 99.95%.
If we take the original set of 85 regions, including excluded Leningrad Oblast, the figure is 87 736 out of 88 799 UIKs, or 98.80%.
This is coverage of the paper-precinct registry, not a share of all voters in the country.

</details>

Several input-data versions were saved in advance to check how much the result depends on updates and discrepancies between sources.

<details>
<summary>Why does the study use several versions of the input data?</summary>

For 88 unambiguously matched UIKs, two saved sources disagreed on some values. Alternatives were saved in advance so that a convenient version would not be chosen after looking at results.

Four versions existed before the calculations:

- primary — the original saved dataset
- S1 — remove all 88 disputed UIKs
- S2a — retain these UIKs but use the Neshodilina values for them
- S2b — retain the primary dataset but apply two later corrections that appeared in the updated version

These 88 precincts were later checked separately against current official CIK protocols. That check found no new disputed values outside the already saved variants.
In 86 cases, the current official protocol matched the primary side of the comparison on the previously disputed values. The other two cases matched the alternative version, and these were exactly the two later revisions already represented in S2b.
There was therefore no need to recalculate the revealed models after this check.

In more detail:

- 68 UIKs matched the primary saved version completely on all 14 checked values
- in another 18, all previously known primary-version values matched, while the previously missing invalid-ballot count was zero in the current official protocol
- 2 UIKs matched the alternative version completely, and these were exactly the two later revisions already represented in S2b
- no cases requiring another numerical version were found

In other words, S2b already contained both later numerical corrections subsequently confirmed by current official protocols. But **S2b is not an exact copy of the current CIK data**.
For example, in those 18 rows, the old saved dataset still has an unknown invalid-ballot count, while the current official source has zero.

This check answers only a question about the provenance of data versions. It does not explain why values changed in the past and says nothing by itself about the mechanism of those changes.

</details>

## How can one table produce different answers?

Imagine that we have the same set of precinct results.
What do we need to decide before any “adjusted” number can appear?

For example:

- whether to compare each precinct with similar nearby precincts or consider the whole country at once
- whether to use the lower part of the distribution as a reference and, if so, which part
- whether to compare one party with the others or recalculate all parties at once
- whether to preserve the total number of valid votes
- what to do with negative deviations
- whether to calculate the model separately by region, by territorial election commission (TIK), or for the whole country
- what happens to precincts for which no comparison could be constructed

Each choice changes the question being asked.
Below, we will therefore compare models not only by their final number, but also by **the rule that produces it**.

And we can ask of each rule: why was this one chosen?
The reasons for choosing rules in this study varied. Sometimes the aim was to reproduce a published method as closely as possible.
Sometimes a public description left a gap that had to be filled.
And some variants were introduced from the outset solely to test sensitivity: to see how much the result depended on that decision at all.
So “fixed in advance” and “justified” are not the same thing.
For each substantial choice, it is therefore useful to distinguish three questions:
**what motivated it, whether it was fixed before the corresponding result was viewed, and how much the answer changes under another variant specified in advance.**

<details>
<summary>Where the main rules came from and what was tested</summary>

### A/B/C

A/B/C were developed entirely within this study. There is no external method that we were trying to replicate exactly.

The default variant was chosen before checking its coverage and before calculating the scenario results:

- the comparison group is drawn from the same TIK, within the 25–50% rank range
- precincts from the 75th percentile upwards are treated as targets
- the larger of the compared precincts can be no more than 1.25 times the size of the smaller one
- at least five comparison precincts are required
- no single comparison precinct can contribute more than half the comparison group's valid votes

The 25–50% range defined a simple lower comparison group.
The upper quarter provided a fairly broad but clearly separated target area.
The 1.25 limit imposed a tighter match in precinct size, while the minimum of five precincts imposed a stricter comparison-group threshold.

Numbers such as 75%, 1.25 or five precincts are not universal statistical constants.
That is why alternatives were specified alongside the default variant in advance:
a wider comparison group, a higher target-area boundary, a looser size restriction and a minimum of three precincts instead of five.
This produced 16 combinations.

The strength of the transformations also varies separately. A grid of 0, 0.25, 0.5, 0.75 and 1 was specified in advance for two operations: from no change at all to full application of the rule, with several intermediate levels.
This grid tests how the answer changes with the strength of the transformation. The step of 0.25 has no deeper substantive meaning.

### D

D is a project adaptation of the broad “party versus the rest” idea associated with Kobak, Shpilkin and Pshenichnikov, not an exact replication of a published program.
The calculation itself is explained in detail below. Here, it is worth explaining why the baseline variant D0 is set up as it is.

D0 fixes three main choices, which are then tested through alternatives:

- the calculation is performed separately for each region
- the lower area contains roughly 20% of the region's valid votes
- precincts are grouped into intervals 0.5 percentage points wide

20% serves as a baseline between the predefined alternatives of 10% and 30%.
The 0.5 pp interval is the finer of the two tested binning options.
The regional level is used as the baseline geography and is separately compared with a more local calculation by TIK.

None of these choices is a universal constant of the method, and D0 is not considered “more correct” than the other variants.
Its purpose is to provide a specific starting point against which sensitivity can be checked.

To avoid relying on just one such set of decisions without testing it, four further variants were defined in advance.
D1 reduces the lower area to 10%, D2 increases it to 30%, D3 keeps 20% but changes the interval width from 0.5 to 1 pp, and D4 moves the calculation from regions to official TIKs.

These variants are thus not five competing methods. They test three specific decisions in D: **the size of the reference area, the fineness of the binning and the geographical level of the calculation**.

### Important Stories

Here the starting point is a published rule. The authors explicitly name a reference area of 20–29%, so the default project variant implements it as the window `[20%, 30%)`.
But the exact implementation of the coefficient and the final recalculation is not fully published.
Our version is therefore a reconstruction with missing rules specified in advance, not a claim to have reproduced the original code exactly.

The choice of reference window is one of the method's most visible assumptions.
So, before looking at the results, a bounded grid of 15 windows was specified: starting points of 10%, 15%, 20%, 25% and 30%, with widths of 5, 10 or 15 percentage points, for the combinations included in the grid.
Their purpose is not to find the window that gives the most convincing percentage, but to test the result's dependence on the choice of reference.

Other possible options, such as how to estimate the coefficient or handle negative deviations, change the calculation itself rather than a single parameter within the chosen implementation.
They were therefore not included in the main grid of variants.

### Cedar

Cedar is different: its public code describes the calculation algorithm but does not specify a unique way to apply it to the 2026 election.

The algorithm can automatically suggest a reference interval,
but in the [published notebook with federal calculations for 2020 and 2024](https://github.com/Cedar-Russia/electoral_statistics/blob/30b1b6ae4725e7307f67975bc122f35049864644/Electoral%20statistics.ipynb)
that choice was then manually overridden.
There is no such published decision for 2026.
The default project variant therefore uses the public automatic selection rule without a new manual override. This is an adaptation: we did not choose our own reference interval after seeing the result.

Because the published calculations for 2020 and 2024 show that the interval's location could in practice be set manually,
a separate test was defined in advance using all fixed 1-pp intervals with right edges from 10% to 80%.
This is neither a search for the “correct” reference interval nor a confidence interval. It tests sensitivity to precisely the part of Cedar that could be set manually in the published calculations.

### Novaya Gazeta Europe's one-dimensional model

Some rules are reasonably clear from the published chart:

- the horizontal axis uses the focal party's result
- the histogram height represents that party's vote mass, not simply the number of UIKs
- three Gaussian components are used
- the authors interpret the component with the lowest center as the “core”

Our reconstruction therefore fixed three components and the same principle for selecting the core component.
The exact fitting source code, bin width and several other technical details have not been established.
The project therefore chose one explicit fitting procedure and tested three predefined histogram widths: 0.5, 1 and 2 percentage points.

The minimum allowed component width changes together with the histogram binning, so this is not a pure test of binning alone.

Component counts of 2 or 4 could also have been tested, but that changes the model's structure rather than just its technical detail. Those variants were deliberately left out of the current grid.

### Novaya Gazeta Europe's two-dimensional model

The publication establishes the basic construction: a UIK is a point in “participation level × party result” space, the model uses three two-dimensional components, and the published threshold for membership in the selected core is above 50%.
The component count and the default 50% threshold were therefore retained in the reconstruction.
But I could not find the exact component shape, coordinate scaling, observation weights, initial conditions or other implementation details in the available public material.
The study therefore does not present these details as having been recovered exactly.

The default project version uses one component shape fixed in advance.
An alternative shape is tested separately. Membership thresholds of 50%, 70% and 90% test how the set of UIKs assigned to the already fitted component changes.
They require no new fit and do not change its center.

### Shared checks for the additional methods

For the four executable external methods, four input-data versions saved in advance were tested separately. This helps distinguish source sensitivity from sensitivity to model rules.
Another shared check leaves out one region at a time. Its purpose is not to find a “suspicious” region, but to see how much the result depends on the presence of each large part of the dataset.

No full cross-product of all possible settings was constructed. The main grid is deliberately bounded: otherwise the number of combinations grows rapidly, and sensitivity testing turns into a practically unlimited set of models.

</details>

But there are more subtleties.
Several published works use the expression “Shpilkin method”,
but it is not the name of one fixed program that can be run on a new election without further decisions.
The broad idea is to compare the distribution of votes for the selected party with votes for the others
and use some lower part of the distribution as a reference.
But specific public implementations differ in important details:
**where to obtain the reference, how to estimate the proportion, which geography to use and what to call the output**.
Those differences will be demonstrated below.

## What should we do with statistically unusual structures?

Before the scenario recalculations, the data were separately examined for statistically unusual structures (or “anomalies”).
Examples included relationships between ballot-issuance intensity and party shares, or between the shape of interim results on 18–20 September and the final totals.

One of the clearest ways to see such a structure is a two-dimensional chart positioning each UIK by participation level and the selected party's result.
Distributions of this kind play an important role in the work of Dmitry Kobak, Sergey Shpilkin and Maxim Pshenichnikov.

The chart may show a main concentration of precincts and an elongated structure extending towards both higher turnout and a higher party result.
On such charts, the area containing most precincts is often called the “core”. The structure extending up and to the right is called the “comet tail”.

Figure placeholder: two-dimensional density of UIKs in the primary dataset — horizontal axis: ballots issued / registered voters, vertical axis: focal-party share of valid votes

> What the chart directly shows is the shape of the distribution. The main concentration and elongated structure describe the data. They are not a ready-made estimate of the number of altered votes or a classification of individual UIKs as “honest” or “dishonest”.

Here we need to distinguish observation from interpretation.
The chart itself can show that the distribution changes shape and that the party result is associated with participation level.
But that does not yet yield a value we can call an alternative result.

To move from visible structure to a numerical estimate, we need a “counterfactual reference”: we must decide which area to use as a reference and which relationship to expect beyond it.
Then the familiar choices arise: one interval or several, the country as a whole or separate territories, whether to retain negative deviations, and which precincts to include at all.

It is at this step that one visual picture turns into several different calculation methods.
That is why so much attention below goes to calculation rules: a striking chart shape does not tell us where to place the reference line or how to measure deviations from it.

At this point, two problems need to be distinguished.
The first is that **statistical unusualness is not a label saying “this UIK's count has been distorted by N votes”.**
An association between features does not by itself establish a specific mechanism, a number of added or redistributed votes, or an alternative precinct result.

The second, perhaps more important, problem is that if we first label precincts “anomalous” from their final votes and then recalculate those same votes using that label, we can build part of the conclusion into the selection rule.
For example, if precincts are considered unusual precisely because of a high party result, and that result is then reduced only at those precincts, a lower total partly follows from the definition of the selected group.
The main scenarios below therefore do not use earlier statistical signals as a list of precincts to be “corrected”.

Later, a separate examination asked whether it was possible to define a scenario that uses the unusual structures found in the data to select precincts for an alternative calculation.
That branch did not reach model implementation or real data.

<details>
<summary>Why was the anomaly-aware model stopped before real data?</summary>

The examination did not reach model implementation.
Two artificial examples with a known data construction were considered.

Ordinary heterogeneity and a deliberately introduced change turned out to be capable of producing the same observations.
From such data alone, we cannot guarantee that we can distinguish the cases while also requiring a rule to avoid an unwarranted correction in the first case and recover the original state in the second.

The branch therefore stopped at requirements analysis and mathematical counterexamples, before model testing or application to real data.
This is a bounded negative result for the constructions examined, not proof that all models of this kind are impossible.

</details>

## Which calculation families are compared?

Setting technical names aside, we have three broad groups of models answering three different kinds of question.

### 1. What if we compare a precinct with similar precincts nearby?

These are A, B and C. For a selected precinct, a comparison group is sought within the same territorial election commission (TIK). The scenario then changes either the distribution of votes among parties, the overall scale of related counts, or both.

### 2. What if we compare one party with all the others combined?

This is the broad idea associated with the work of [Dmitry Kobak, Sergey Shpilkin and Maxim Pshenichnikov](https://arxiv.org/abs/1205.0741) and later implementations.

One party is selected as the focus of the calculation (the **focal party**). Its votes are compared with all other parties' votes combined, using some lower part of the distribution as a reference.

In essence, this continues the geometry shown above: we see a comet tail, but the calculation begins when we decide what relationship to use as a reference and how to extend it beyond the reference area.

It matters, though, that the “Shpilkin method” does not by itself specify a unique program.
For example, [Cedar](https://github.com/Cedar-Russia/electoral_statistics) uses one reference interval and historically changed it manually for particular years.
[Important Stories](https://istories.media/stories/2026/09/22/bolee-18-iz-30-mln-bumazhnikh-golosov-za-edinuyu-rossiyu-mogli-bit-sfalsifitsirovani/), meanwhile, explicitly names a different reference for 2026: the 20–29% range.
In both cases, some details cannot simply be transferred to our dataset without further decisions.

That is why model D was introduced in the study: not as a “corrected” version of someone else's method, but as **a separate, fully described adaptation of the same broad idea**,
with rules fixed in advance for constructing the comparison, choosing the lower part of the distribution, estimating the proportion and handling cases where the calculation cannot be defined.

The conventional calculation for which [Novaya Gazeta Europe](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty) reports around 25% also belongs to this broad family.
But I could not find enough detail in the available public material to reproduce that calculation exactly.

### 3. What if, instead of recalculating every vote, we look for a characteristic area of the distribution?

The same [Novaya Gazeta Europe article](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty) contains several constructions that address a different task.
They examine either the distribution of precincts by party result or the cloud of precincts by party result and participation level, and try to identify a characteristic area that they call the “core”.

One variant compares the ratio of votes for the selected party to the combined votes for the other parties around this core. That is where the published 34% comes from.
Two others use **[Gaussians](https://ru.wikipedia.org/wiki/Нормальное_распределение)**: curves that can describe concentrations of values around a center.
Several Gaussians can represent a complex chart as several overlapping parts.

Statistically, 33% here appears as the center of one of the fitted components. Novaya Gazeta Europe calls this component the “honest core”, so its center is used as an estimate of United Russia's result without fraud.
That is the meaning of the published 33%: in the authors' assessment, the party's result without fraud is around that level.

Two things need to be separated here. First, the statistical model identifies a component and estimates its center at around 33%.
The authors then interpret the component as the “honest core” and use the fitted center as an estimate of the party's result without fraud.
I am drawing attention to this not to dispute the interpretation, but to show where the direct calculation result ends and its substantive interpretation begins.

Below, it is therefore important to distinguish two questions: “what would the party's share be after a scenario recalculation?” and “where on the chart is the center of the part the model calls the core?”

And once again: this is not a competition between methods, or an attempt to show that the study's own calculations are “more scientific” or “more correct” than published ones.
Public works are used here only as examples of different ways to turn data into a result. The project's own implementations make the rules explicit and test how much the answer depends on them.

## A/B/C: local comparison of precincts

A, B and C use the same logic to select comparison precincts, but change different parts of the data.

A changes the distribution of valid votes among parties.
The total number of valid votes at a precinct stays the same, while party shares move towards those in the selected comparison group.

B changes the scale of the counts.
The number of ballots issued moves towards the comparison group's level.
The related counts — valid votes and votes for all parties — are scaled proportionally along with it.
Party shares within the precinct stay the same.

C applies both changes at once.

### In plain terms?

A: keep the same number of votes, but distribute them among parties roughly as at similar nearby precincts.

B: keep the party proportions, but bring the total volume of the related counts closer to that at similar precincts.

C: apply both rules.

### How are comparison precincts selected?

A/B/C use the ratio of **ballots issued to registered voters**.
To avoid confusing it with other definitions of turnout below, we will call this measure **issuance intensity**.

Within each TIK, precincts are ranked by this measure.
A precinct's position in that list is called its **issuance-intensity rank**.
For example, a rank of 75% does not mean “ballots were issued to 75% of voters”. It means that the precinct's value is roughly above those of three quarters of the precincts in its TIK.

In the default version, the model attempts to recalculate the top quarter of the list — precincts with ranks from 75% upwards.
The comparison group comes from the same TIK, but from the 25–50% rank range.

Comparison precincts are also restricted by size: the larger one cannot be more than 1.25 times the size of the smaller one.
There must be at least five suitable precincts. In addition, no single precinct may contribute more than half of the comparison group's valid votes.

These rules do not prove that the precincts become fully interchangeable. They only define a transparent comparison mechanism.

Of the 87 736 UIKs, 22 103 enter the upper target group in the default version.
After the other conditions are applied, an admissible comparison can be constructed for 5 391 UIKs.

We will call this group of 5 391 UIKs the **A/B/C model support**: these are simply the target UIKs for which the model's specified comparison group is defined.
The term does not mean that the other precincts are “normal”, or that these have been proven comparable.

For precincts outside this group, the model invents nothing: their original values remain in the overall total.

<details>
<summary>Why do A/B/C change only 5 391 of the 87 736 UIKs?</summary>

| Step | Remaining | Why some precincts dropped out |
|-----------------------------------------------------------------------|---------:|-------------------------------------------------------|
| All UIKs in the primary dataset | 87 736 | — |
| Issuance-intensity rank ≥75% within their TIK | 22 103 | 65 633 are outside the upper target group |
| At least one comparison precinct of a suitable size exists | 15 586 | 6 517 had none of a suitable size |
| At least five suitable comparison precincts | 5 391 | 10 195 had fewer than five |
| The group's sum of valid votes is positive | 5 391 | no additional exclusions |
| No precinct contributes more than half of the group's valid votes | 5 391 | no additional exclusions |

In total, 16 712 of the 22 103 target UIKs fell outside model support: 6 517 because there were no comparison precincts of a suitable size,
and another 10 195 because there were too few.

</details>

<details>
<summary>Other predeclared versions of the A/B/C rules</summary>

In total, 16 combinations of four choices were fixed before the results were calculated:

| Parameter | Version 1 | Version 2 |
|------------------------------|--------------------|-------------------|
| Comparison-group range | 25–50% of ranks | 25–62.5% of ranks |
| Upper target-group threshold | from 75% | from 87.5% |
| Permitted size difference | ratio 0.8–1.25 | ratio 2/3–1.5 |
| Minimum comparison precincts | 3 | 5 |

The default version uses the 25–50% range, target precincts from 75%, a size ratio of 0.8–1.25 and at least five comparison precincts.
It was chosen before coverage was checked and before scenario results were calculated.

</details>

### What did A/B/C produce?

In the default version, recalculation takes place only at the 5 391 precincts for which the model's specified comparison group could be constructed. The original values remain at the other 82 thousand-plus UIKs.

The shifts across the whole dataset are therefore relatively small: the model changes only a limited part of it. This is clear in the ten-party table near the beginning.

Figure placeholder: observed results and A/B/C — changes for all ten parties

<details>
<summary>Exact calculated A/B/C values for all ten parties</summary>

| Party | Observed | A | B | C |
|--------------------------|-----------:|--------------:|--------------:|--------------:|
| Rodina | 355 312 | 359 639.04 | 348 803.70 | 351 546.10 |
| United Russia | 32 143 992 | 31 930 987.55 | 31 583 196.16 | 31 449 106.64 |
| Communist Party of the Russian Federation | 7 983 282 | 8 076 756.69 | 7 844 414.84 | 7 904 488.40 |
| Pensioners' Party | 1 044 022 | 1 063 680.08 | 1 026 587.53 | 1 039 190.45 |
| New People | 4 159 960 | 4 203 756.64 | 4 078 613.22 | 4 105 210.00 |
| Party of Direct Democracy | 190 862 | 190 981.10 | 187 165.39 | 187 183.80 |
| Greens | 523 717 | 528 297.25 | 513 227.29 | 515 991.69 |
| Communists of Russia | 438 044 | 443 274.87 | 430 080.61 | 433 683.97 |
| Liberal Democratic Party of Russia | 5 086 868 | 5 116 570.69 | 4 995 304.77 | 5 014 661.58 |
| A Just Russia | 2 797 142 | 2 809 257.09 | 2 739 756.84 | 2 746 087.69 |

Calculated values can be fractional because they are mathematical quantities, not a claim that a “fractional ballot” exists.

</details>

<details>
<summary>How is the strength of A and B controlled?</summary>

To go beyond just “change nothing” and “apply the rule in full”,
a grid of 0, 0.25, 0.5, 0.75, 1 was fixed in advance for the two transformations.

The parameter λ sets the strength of the change in the party distribution.
The parameter μ sets the strength of the scaling of ballots issued and the related counts.

For one party, a fixed data version and one set of rules, the following exact decomposition holds:

`Q(λ,μ) = Qисх + λKсостав + μKобъём + λμKвзаимодействие`.

The last term is a purely arithmetic interaction between the two recalculations, not evidence of an interaction between any real causes.

</details>

### How much do A/B/C change under other predeclared rules?

To compare the sensitivity of different families using one measure, we will sometimes use United Russia's share below: it is the focal party in the single-party models, but this does not change the ten-party meaning of A/B/C.

On the primary data version, its calculated share across the entire predeclared A/B/C grid lies between 57.96% and 58.76%.

Why is this so far from the published 25–35%? First of all, because A/B/C do not recalculate every precinct in the primary dataset.
In the default version, they actually change only the 5 391 precincts where a local comparison could be constructed. The original data remain at the others.
Of all 87 736 precincts, only 22 103 even enter the upper target group under the default A/B/C rule. For most of those, it is then impossible to find a sufficiently large comparison group in the same TIK and of a suitable size. Recalculation is ultimately defined for 5 391 UIKs.
The detailed selection sequence is shown above, under “Why do A/B/C change only 5 391 of the 87 736 UIKs?”.
Moreover, some of the 33–34% values discussed below are not recalculated national shares at all, but statistical component centers.

This range therefore does not contradict the lower numbers from other constructions: they answer different questions.

Nor is it a confidence interval or a range within which “the truth must lie”.
It is simply the minimum and maximum among predeclared calculation variants.

<details>
<summary>Full A/B/C spread for the focal party across four data versions</summary>

| Version | Mode | Calculated count: minimum — maximum | Share: minimum — maximum |
|----------|-------|------------------------------------:|-------------------------:|
| primary | A | 31 720 009 — 32 143 992 | 57.9645% — 58.7392% |
| primary | B | 31 139 828 — 32 143 992 | 58.6631% — 58.7626% |
| primary | C | 30 860 570 — 32 143 992 | 57.9645% — 58.7626% |
| S1 | A | 31 699 226 — 32 123 772 | 57.9909% — 58.7676% |
| S1 | B | 31 120 327 — 32 123 772 | 58.6908% — 58.7914% |
| S1 | C | 30 840 648 — 32 123 772 | 57.9909% — 58.7914% |
| S2a | A | 31 730 869 — 32 156 087 | 57.9843% — 58.7613% |
| S2a | B | 31 151 060 — 32 156 087 | 58.6848% — 58.7851% |
| S2a | C | 30 870 931 — 32 156 087 | 57.9843% — 58.7851% |
| S2b | A | 31 719 483 — 32 143 653 | 57.9635% — 58.7386% |
| S2b | B | 31 139 483 — 32 143 653 | 58.6626% — 58.7619% |
| S2b | C | 30 860 059 — 32 143 653 | 57.9635% — 58.7619% |

The minimum vote count and minimum share need not occur in the same scenario,
because B and C change both the numerator and the total volume of valid votes.

</details>

## One party versus the rest: one idea, several implementations

We now turn to the family in which one focal party is compared with the sum of the others.

Here it is particularly easy to start reading the numbers as a competition: one author gets 25%, another 35%, D gets 52–56%.
Different implementations use different data, different reference points and even different types of output.
I am not trying to declare any of them correct.

### Cedar: one reference interval

The [Cedar](https://github.com/Cedar-Russia/electoral_statistics) project publishes an implementation and a separate [methodology description](https://www.cedarus.io/research/evolution-of-russian-elections).

In simple terms, the model works as follows.
Precincts are placed into narrow intervals by their level of participation.
In one of these, the ratio of the focal party's votes to the others is taken.
The model then effectively asks: **“if we use this ratio as a reference, how many votes for the focal party would we expect at the other participation levels?”**
The difference between the observed and expected curves is then summed.

The choice of reference interval is particularly important here.
Cedar can suggest one automatically,
but in the [published notebook with federal calculations for 2020 and 2024](https://github.com/Cedar-Russia/electoral_statistics/blob/30b1b6ae4725e7307f67975bc122f35049864644/Electoral%20statistics.ipynb)
that choice was subsequently overridden manually.
In addition, [Cedar's methodology description](https://www.cedarus.io/research/evolution-of-russian-elections) includes manual decisions about which regions the method is applicable to at all, and the published code has no universal algorithm for this selection.

So “simply applying Cedar to 2026” is not possible without making new decisions.
A separate adaptation was fixed in advance for this study: use the public automatic reference-interval selection rule without a new manual override, and explicitly define the input-data rules.

In the default version, automatic selection gave the interval (43%, 44%]. The resulting residual equals 41.74% of the focal party's observed votes.

What does that mean? The model constructs an expected vote count for the focal party using the selected reference, then compares it with the observed count.

Figure placeholder: Cedar observed and expected curves with the selected 43–44% reference interval

> One narrow reference interval sets the scale of the expected curve. Selecting this area is therefore part of the calculation itself, not a decorative chart setting.

Imagine a simple example: party N received 100 votes, while the other counted ballots amounted to 200.
Using the ratio between the party and the other ballots in the selected reference interval, Cedar might say: given these 200 ballots, the model would expect, for example, 58 votes for N.
The difference between the actual 100 and the model's 58 is 42. Dividing it by the party's actual 100 votes gives 42%. This is the measure that constitutes the main output of this calculation.

For comparison, we can extend the example to the party's share of all counted ballots. Before recalculation, it received 100 out of 300, or 33.3%.
If we replace the actual 100 votes with the model's 58 and leave the other 200 unchanged, we get 58 out of 258, or about 22.5%.

The difference between the two numbers is now visible. The 42% shows what fraction of the party's observed votes the model residual represents. The 22.5% would be its conditional share after an additional recalculation.
Cedar publishes the first measure as its main output, and our adaptation uses the same metric.

If the model expects more votes than are observed under the selected reference, the residual becomes negative.
A negative value therefore does not mean “negative fraud” or a proven undercount either — it is simply a property of the formula.

The Cedar adaptation does not apply to all 87 736 UIKs: only 71 438 enter the calculation.
Another 16 298 are not included: 2 758 because they have no more than 100 registered voters, and 13 540 because the number of invalid ballots is unknown in the stored dataset.

The choice of reference interval ultimately proved very important.
The predeclared check used every fixed interval with a right edge from 10% to 80%.
The residual ranged from −48.63% to 95.72% and crossed zero as the reference interval passed roughly 60%.

Why is the spread so large?
Because one small reference interval sets the scale of the entire expected curve.
Changing that interval changes the initial ratio between the focal party and the others, and the entire curve is recalculated with it.

This is not an uncertainty interval around 41.74%, but a check of how much the result depends specifically on the choice of reference.
The reference intervals themselves also differ greatly in size: in the primary curve they contain from 1 to 1 420 UIKs.
Next to each point, the chart shows the size of the reference interval and the total votes for the focal party and the others on which this ratio is based.

Figure placeholder: Cedar result at different reference intervals, with UIK counts and vote volumes in each interval

<details>
<summary>Technical outline of our Cedar adaptation</summary>

The coordinate here differs from A/B/C and D: it uses `(valid + known invalid ballots) / registered voters`.

Intervals are 1 percentage point wide. For the selected reference interval, the ratio is taken between the focal party's votes `L` and the other ballots under Cedar's definition `O`:

`α = L / O`.

An expected `L* = α · O` is then constructed for each interval, and the total residual is the signed sum of `L − L*`.

Automatic reference selection in public Cedar uses smoothing and fitting of two Gaussians, but in the [published notebook with federal calculations for 2020 and 2024](https://github.com/Cedar-Russia/electoral_statistics/blob/30b1b6ae4725e7307f67975bc122f35049864644/Electoral%20statistics.ipynb) the selected interval is subsequently overridden manually.
This is precisely why our 2026 version is called an adaptation, rather than an exact replication of a nonexistent public “Cedar-2026”.

</details>

### Important Stories: the 20–29% reference range

[Important Stories](https://istories.media/stories/2026/09/22/bolee-18-iz-30-mln-bumazhnikh-golosov-za-edinuyu-rossiyu-mogli-bit-sfalsifitsirovani/) applied a similar general idea to a different dataset.

Their calculation used the data available on the evening of 21 September, when about 94% of protocols were available.
Moscow was excluded entirely, and DEG in 32 regions was not counted. The authors explicitly specified 20–29% as the reference area.

The public article, however, does not disclose enough detail to independently reconstruct the exact coefficient formula within that range or all the final accounting rules.
A version of this idea was therefore fixed in advance for this study: “20–29%” was technically implemented as a range from 20% inclusive to 30% exclusive.

The default version on our dataset gives 38.00%. Important Stories published about 35%.

This discrepancy should not be read as an error of three percentage points.
The comparison involves different data snapshots and implementations that are not fully identical: the authors used an earlier snapshot, excluded Moscow and DEG, and I could not reconstruct some of the calculation rules from the available public material.
Our 38% is the result of a specified project version of this idea, not a claim to have exactly reproduced the published 35%.

Figure placeholder: observed votes for the focal party and the others by participation level, the expected curve of the project reconstruction, and the highlighted 20–30% reference range

> The visible shape of the distribution does not determine a numerical estimate by itself. Here the calculation uses the 20–30% range as a reference for the expected relationship.
> Below we show how much the answer changes when a different predeclared range is selected.

To test how much the result depends specifically on the reference area, 15 ranges were specified before the results were viewed. Their answers range from 36.33% to 43.64%.

These variants draw on very different numbers of UIKs: from 141 in the smallest range to 17 501 in the largest.
So 36.33–43.64% is not a confidence interval, but simply the spread of answers under different predeclared rules for choosing the reference.

<details>
<summary>All 15 reference ranges for the calculation inspired by Important Stories</summary>

| Range | Share | UIKs in reference group |
|-----------|-------:|---------------------:|
| [10%,15%) | 41.49% | 141 |
| [10%,20%) | 43.37% | 846 |
| [10%,25%) | 41.83% | 1 909 |
| [15%,20%) | 43.64% | 705 |
| [15%,25%) | 41.85% | 1 768 |
| [15%,30%) | 39.17% | 3 749 |
| [20%,25%) | 40.63% | 1 063 |
| [20%,30%) | 38.00% | 3 044 |
| [20%,35%) | 37.41% | 7 026 |
| [25%,30%) | 36.33% | 1 981 |
| [25%,35%) | 36.78% | 5 963 |
| [25%,40%) | 38.14% | 12 201 |
| [30%,35%) | 36.98% | 3 982 |
| [30%,40%) | 38.44% | 10 220 |
| [30%,45%) | 40.78% | 17 501 |

</details>

### D: another version of the same general idea

A disclaimer: D is not an “improved Cedar” and is not intended to correct or refute other people's estimates.
It is simply another conditional scenario from the same broad family. Its purpose is to make all the necessary choices explicit and see what follows from that set of rules.

Simply saying “we use Shpilkin's method” leaves important questions open: which part of the distribution to use as a reference, whether to calculate for the whole country or separate territories, how to estimate the proportion,
whether to retain negative deviations, and what to do where the model cannot construct an admissible result.

In D, these choices are specified in advance. The focal party is compared with the sum of the others separately within geographic groups.
In D0–D3, those groups are regions, and in D4 they are official TIKs.
The lower part of the distribution is used to estimate the usual ratio between the focal party and the others. That ratio is then extended to the higher part.

In the default D0 version, the lower area contains roughly 20% of the corresponding region's valid votes.
Four other predeclared variants change the size of this lower area, the interval width or the geographic level.

Results on the primary data version:

| Variant | Where calculated | Calculated focal-party share |
|---------|----------------------------------|--------------------------------:|
| D0 | regions, default version | 53.25% |
| D1 | regions, smaller lower area | 52.13% |
| D2 | regions, larger lower area | 53.94% |
| D3 | regions, wider intervals | 52.60% |
| D4 | TIKs | 56.07% |

These 52–56% are not a “scientific correction” to the published 25–35%.
D uses different geography, a different reference-selection rule, a different estimate of the proportion and its own applicability rules.
Its result must be read together with those conditions.

In the default D0 version, a scenario could be constructed for 53 of the 84 regions, containing roughly 62% of the dataset's original valid votes. For the other regions, the original values remain in the overall total.

<details>
<summary>Why is D not defined for every region and TIK?</summary>

D cannot always construct a scenario for a given territory. Sometimes there are too few precincts in the lower reference area. Sometimes no precinct remains above it to which the rule can be applied. In some cases, the formula produces a set of counts that fails basic arithmetic checks.

In D0, the calculation is defined for 53 of the 84 regions.

In D4, the calculation is performed across 2 818 TIKs:

- 1 454 pass every check
- 998 have too little data in the reference area
- for 12, no precinct remains beyond the reference area to which the rule can be applied
- for 354, the formally constructed variant produces an incompatible set of counts and is therefore not used

The 1 454 applicable TIKs contain 67.48% of the original valid votes.

“Undefined” means only one thing here: under these rules, the model could not construct an admissible scenario value for this group.

</details>

<details>
<summary>How D is calculated</summary>

Precincts within a region or TIK are grouped into intervals by the ratio `ballots issued / registered voters`. In the technical sections, such intervals are called **bins**.

The parameter `q` determines which lower fraction of valid votes enters the fitting area.

| Variant | Rule |
|---------|--------------------------------------|
| D0 | region, q=20%, bin 0.5 pp |
| D1 | region, q=10%, bin 0.5 pp |
| D2 | region, q=30%, bin 0.5 pp |
| D3 | region, q=20%, bin 1 pp |
| D4 | official TIK, q=20%, bin 0.5 pp |

If `f` is the focal party's votes and `g` is the sum of the others, the proportionality coefficient is fitted through the origin:

`α = Σ(fg) / Σ(g²)`.

The signed deviation `f − αg` is then calculated in the upper part. Positive and negative deviations can offset each other.

Where D is defined, votes for the other nine parties are retained, but the calculated number of focal-party votes and the total volume of valid votes change.
D therefore does not create an alternative ten-party result for each individual UIK.

</details>

### Novaya Gazeta Europe's published calculation of about 25%

The [Novaya Gazeta Europe article](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty) mentioned earlier describes a conventional “one party versus the rest” construction.
The authors write that such a calculation would give about 25%.
They then turn to other ways of identifying the “core”, because they consider the simple version a poor match for the observed structure of the 2026 data.

In the available public material, I could not find the exact reference range, scaling formula, complete separate dataset or final accounting rules for that calculation.
I therefore did not fill the gaps with guesses or choose an implementation to match the published 25%.

## “Core” models: when the percentage no longer means a recalculated result

In [Novaya Gazeta Europe's article](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty), about 34% is obtained not only through a “one party versus the rest” scheme.
The authors consider several ways of finding an area of the distribution that they call the “core”.

It is important not to mix up two meanings of this word.
On a two-dimensional chart, “core” can refer to the area where precincts are mainly concentrated.
But in the one-dimensional and two-dimensional reconstructions below, the “core” is a specific component of a statistical model, selected by a predeclared rule.

These ideas are related, but have different mathematical definitions.
Below, the word “core” is used only in the sense defined by the method being discussed.
It does not mean that the precincts within it have been proven “honest”.

### Comparison around the core: about 34%

In the first version, the authors examine the precinct distribution by turnout and party result, exclude Moscow and additional regions
where, in their interpretation, the result changed without a corresponding increase in turnout, and compare the ratio of party votes to the others around the selected core.

The published level is about 34%.

But in the available public material, I could not find the exact core boundary, the full list of excluded regions or the formula used to estimate the ratio.
This approach therefore remained a description of a published construction in this study, without a project calculation.

In my view, these 34% are better read as a level of voter support corresponding to the core selected by the authors, rather than as a published full recalculation of every UIK and all ten parties.

### The one-dimensional model: three Gaussians

In the second version in the same publication, precincts are grouped by the focal party's result.
But the height of each bar shows not the number of UIKs, but how many votes for that party come from precincts whose results fall in the corresponding range.

The shape is then described by the sum of three Gaussians. In the published chart, their centers are roughly at 33%, 60% and 93%.
The authors interpret the component with the lowest center as the “core”. This does not follow automatically from the mathematics itself. It is the authors' substantive interpretation.
In our reconstruction, this had to be turned into a rule, so we fixed it in advance: the component with the lowest center is treated as the core.

We need to introduce another term here — **fitting**. This means choosing the parameters of mathematical curves so that they describe the observed shape of the data as closely as possible.
It should not be confused with choosing a result to match a number desired in advance.

What does an output such as 35.23% in our reconstruction mean? Not “the party would have received 35.23% nationally”.
It is not a result for a preselected group of precincts. The model uses the whole chart and tries to describe it with three components.
One of them has a center around 35.23%. In other words, the model sees a separate peak within the overall picture, around precincts where the party's result is roughly 35%.

There are two levels at which this number can be read. The most cautious statistical conclusion is that a component with a center around 35.23% is identified in the data.
The second level is substantive. If, as Novaya Gazeta Europe does, we treat this component as an “honest core”, its center can then be read as an estimate of the party's result without fraud.
The mathematical fit itself does not establish why this component exists or whether it must specifically be associated with the absence of fraud. Our study does not test that separate question.

I could not find the exact source code for this fit in the available public material, so a project version was specified before calculation: three components, histogram height determined by the focal party's votes,
and the center of the component with the lowest result taken as the output.

On the primary data, this center was 35.23%.

Changing the histogram bar width between three predeclared variants gave 35.24%, 35.23% and 35.28%.
Excluding individual regions had a more noticeable effect: across 84 variants, the center ranged from 34.90% to 36.37%, with the largest departure occurring when St Petersburg was excluded.

This does not make 35.23% “more correct” than the published approximately 33%. The published and project constructions differ in their data snapshots and, most likely, in some of the technical details that could not be found.

<details>
<summary>Technical details of the one-dimensional model</summary>

Three components are visible in the published construction, so their number was fixed in advance in our version.

The fit is performed on histogram heights using least squares.

A bar width of 0.5 / 1 / 2 percentage points changes both the histogram partition and the minimum permitted width of a fitted component.
This check therefore cannot be interpreted as changing only one technical parameter.

</details>

### The two-dimensional model: where the “core” is and which precincts the model assigns to it

In our reconstruction, the third version uses two precinct coordinates at once:

- `ballots issued / registered voters`
- the focal party's share of valid votes

Each UIK becomes a point on a plane. The model tries to describe the point cloud with three two-dimensional Gaussians and selects the component with the lowest mean focal-party result as the model “core”.

Here the model answers two questions. First, it estimates where the selected component's center is. In the default project version, this is:

- 38.87% for the ratio of ballots issued to registered voters
- 34.37% for the focal-party share

Then, for each UIK, the model estimates which of the three components the point fits best. A number from 0 to 100% here expresses the probability of membership in a component within the mathematical model itself. It is not the probability that a precinct is honest.

If we require a probability above 50%, the selected component includes:

- 18 904 UIKs
- 28 371 106 registered voters
- 28.55% of the registered voters in the dataset under consideration

Raising the threshold from 50% to 70% or 90% does not change the model itself — we merely become stricter about which points to assign to the component already found.
The number of UIKs therefore falls from 18 904 → 15 802 → 8 086, while the center stays the same by construction.

Changing the shapes of the components themselves, however, requires a new fit.
In the version with axis-aligned components, the center was 39.99% / 35.05%, and at a 50% threshold, 23 041 UIKs were assigned to the selected component.

Novaya Gazeta Europe's published reference values are roughly 38.5% turnout, 33% party result, 18 336 UIKs and about 26.2 million registered voters.
These numbers refer to a different data snapshot and a different implementation, so our small difference cannot be called a “replication error”.

<details>
<summary>What is known about the published two-dimensional model, and what could not be reconstructed?</summary>

The article tells us:

- three two-dimensional components
- Moscow is excluded
- DEG is not counted
- the selected component's center is around 38.5% / 33%
- the membership threshold is above 50%
- 18 336 UIKs and 26.2 million registered voters are in this group

The available public material did not reveal the exact component shape type, coordinate scaling, observation weights, initial conditions, number of repeated runs, regularization or machine rule for selecting the required component.

The project version is therefore called a reconstruction, not an exact copy.

</details>

## What changes if we change one rule?

Below, I use sensitivity to mean a simple check: change one preselected rule and see how much the result changes.

This is not statistical error or an attempt to try every possible model. Only the limited grid of variants specified in advance is tested.

### A/B/C and D

The comparison here uses one common measure — the number of votes for United Russia, because it is the focal party in the single-party constructions.

On the primary data version, the largest spread in A/B/C from changing only the comparison-group selection rules is 892 991 votes. Changing the strength of party-share redistribution gives 423 983, and changing the scaling strength gives 1 004 164.

If the model rules stay the same and only the four stored versions of the source data change, the largest spread in the final calculated count is 32 669 votes.

If we compare not the totals themselves, but only the size of the model adjustment relative to each version's observed result, the spread between versions is 2 032 votes.

For D, differences between the stored data versions are also measured in tens of thousands of calculated votes, whereas moving between its predeclared variants produces differences in the millions.

### Reconstruction of the Important Stories approach

Across the four data versions, the default version changes within 0.52 percentage points.

Changing the reference range among the fifteen predeclared variants produces a spread of 7.31 percentage points — from 36.33% to 43.64%.

Here it is particularly clear that the reference range is not a minor technical setting, but a substantial part of how the problem is defined.

### Cedar

Between the four source versions, Cedar's default result changes by about 0.06 percentage points of its metric.

Excluding one region produces more noticeable shifts, while choosing a reference interval within the tested grid changes the result so much that the residual even changes sign.

This is not a judgment of Cedar's quality. It is a specific finding from the check: **this implementation is highly sensitive to which interval is used as the reference for scaling.**

### The one-dimensional and two-dimensional models

In the one-dimensional model, moving between the four data versions and the three tested histogram-width variants barely moves the center, but excluding individual regions has a more noticeable effect.

In the two-dimensional model, different settings change different things altogether.
Component shape affects both the center and the selected group's membership. With an already fitted model, the membership threshold changes only the group's membership, not its center.

### What can we conclude from this?

In several models, the result changed more with the selected rules or the exclusion of one region than with moving between the four source-data versions.

But it does not follow that data quality is unimportant or that the model always matters more than the data.
Four specific source versions and a limited set of predeclared variants were tested. Other errors or other model definitions are not covered here.

Likewise, the spread between settings is not a confidence interval. It shows only the answers obtained for the variants actually tested.

Figure placeholder: several sensitivity panels — A/B/C, D, Important Stories reference ranges, Cedar reference intervals, 1D and 2D

## So what did the study show?

The study began with a published 34%. In the process, it became clear that the question “why exactly 34?” is itself too crude, if it can even be considered a valid question.

Even within the broad “one party versus the rest” idea, the method's name does not fully determine the calculation.
Cedar uses one reference interval, which was manually overridden in the published calculations for 2020 and 2024. Important Stories specifies a 20–29% range.
D determines the proportion from several intervals separately within regions or TIKs. Novaya Gazeta Europe's calculation of about 25% is described by yet another set of assumptions.

Gaussian “core” models work differently. First, they find a component with a center around 33–35%.
That center can then be given a substantive interpretation. For example, Novaya Gazeta Europe treats the component found as an “honest core” and uses its center as an estimate of the result without fraud.

Another important point follows. Understanding just the formula and the resulting number is not enough.
We also need to understand **exactly how the model's output becomes a claim of some kind**.
For example, a component center is, by itself, a characteristic of a distribution. It becomes an estimate of the result without fraud after that component is given the meaning of an “honest core”.
That step may be substantively justified, but it is not the same thing as the direct output of a calculation.

At the beginning I put this more briefly: the result depends not only on the data, but also on the question we ask of them. Now we can be more precise:

> **A percentage explains almost nothing by itself. To understand a number, first understand the question it answers.**

This does not mean that “you can get any number you want” or that the methods are arbitrary.
On the contrary, comparison becomes meaningful when the calculation rules are stated explicitly, the interpretation of the result is clear, and we can see how the answer changes when assumptions change.

## What follows from this (and what does not)?

The study can show:

- which dataset was used
- which rules were specified for each model
- where the main rules came from and which are project choices
- on which part of the data a particular calculation is defined
- what conditional numbers arise under these rules
- how much they change with the data version, geography and predeclared settings

But this is **not a test of which researcher named the “correct percentage”**.
If our reconstruction differs from a published result, that alone neither confirms nor refutes the source: the methods may differ in their data, applicability and technical choices unavailable to us.

And **no scenario here is declared to be the reconstructed true election result**.

> **What these numbers do NOT mean**
>
> **Statistical unusualness ≠ a proven violation.**
>
> **A positive Cedar residual ≠ an established count of added votes.**
>
> **A negative Cedar residual ≠ a proven undercount.**
>
> **A Gaussian component center ≠ automatically a national party share.**
>
> **A high model probability of component membership ≠ the probability that a precinct is honest.**

At the same time, **the study does not defend the official result or claim that there were no violations or fraud**.
Nor does it try to use these models to prove their scale or a specific mechanism.

The project does not reconstruct voters' intentions in hypothetically “clean” elections or divide individual UIKs into proven honest and dishonest ones.

And even if two models give similar results, they are still not independent confirmation of each other, because they may use related data, similar assumptions or calculate different quantities altogether.

Any final number is therefore best shown alongside answers to five questions: **what exactly was calculated, on which data, why these particular rules were chosen, how the resulting value is interpreted, and how much the result depends on the selected rules.**

## How can you explore this yourself?

That is what the [interactive Scenario Explorer](https://election-2026-explorer.max-tar.chatgpt.site/) is for.

It starts with the observed data and shows only variants that were specified and calculated in advance. You cannot keep turning unrestricted parameters in the browser until an answer you like appears.

For A/B/C, you can immediately see how the calculation changes for all ten parties when the comparison rules and the strengths of the two transformations change.

The “one party versus the rest” models show their own assumptions separately. For the calculation inspired by Important Stories, each reference range is accompanied by the number of UIKs in that group.
For Cedar, the result is accompanied by the 71 438 included out of 87 736, and the volume of data in the specific reference interval.

For the one-dimensional and two-dimensional models, it is particularly important to note that the output is a statistical component center, while in the two-dimensional model the number of UIKs assigned to the component and registered-voter coverage are separate outputs.
Changing the threshold changes these measures. The fitted model itself stays the same.

Two published Novaya Gazeta Europe approaches — the conventional calculation of about 25% and the core-based version of about 34% — remain on the Methods page as descriptions of published constructions.
They have no project result: there was not enough detail for a faithful reproduction.

Next to each number, the site shows:

- which data are used
- which rules are selected
- where the calculation is defined
- what exactly the output is
- what cannot be concluded from it

## Who conducted the research, and how?

I initiated the project, formulated the research questions and made the key methodological decisions.

I did most of the engineering work and some of the analytical work with help from OpenAI models: they helped design and write code, perform checks, find sources, examine results and identify errors.
It would therefore be wrong to create the impression that one person wrote all the code and performed every calculation manually.

At the same time, I made the decisions about **what exactly to calculate, which variants to test and where to stop an unsuccessful branch** separately and before viewing the corresponding results.

## Reproducibility

The main rule was simple: **do not change an already fixed calculation method after seeing its result just to obtain a more attractive number**.

For A/B/C/D, 1 620 calculation cells were planned in advance: 1 600 for A/B/C and 20 for D.
For Cedar, the Important Stories reconstruction and the two distribution models, another 445 variants were fixed separately before their results were opened.

This does not mean that the entire project was conceived and preregistered before any acquaintance with the data.
New questions arose as the work progressed. But within each calculation stage, settings were fixed first and results were opened afterwards.

Fixing them this way protects against choosing settings to match a number already seen, but is not independent proof that the selected rule is better than the others.
That is precisely why predeclared alternatives were tested alongside the default versions, and why an incomplete reconstruction of a rule from someone else's publication is identified as a separate limitation.

The published 25%, 33%, 34% and 35% were known in advance, but were not used to choose the parameters of our implementations.
Comparison with them took place after the rules of the corresponding calculation had been fixed.
If a result did not match, it stayed that way — the parameters were not tuned to obtain the desired number.

Code, settings, checksums, interim reports and result tables have been published with the study.
Sources and exact checksums are retained for third-party raw data snapshots, but the snapshots themselves are not separately republished.
A published number can therefore be linked to a specific data snapshot and specific calculation rules.

## What else was examined during the study?

<details>
<summary>A brief look at branches that did not become the main scenarios</summary>

- **Early ways of comparing similar precincts.** We tested whether the expected party result could be estimated from precincts of similar size and position within a TIK.
These procedures failed their preliminary check on artificial data, so substantive conclusions from real data were not based on them
- **Interim results from 18–20 September.** We tested whether the shape of the trajectory published during voting was associated with final party shares.
An association was found in a group of 3 615 UIKs, 949 TIKs and 80 regions, but it does not show when particular votes appeared or what an alternative result would have been
- **Previous elections in 2011, 2016 and 2021.** The idea was to use past results as a historical reference.
But it was not possible to establish sufficiently rigorously that UIKs remained the same entities between elections, with comparable boundaries and electorates. This branch therefore remained descriptive regional context
- **A more complex hierarchical model.** It was intended to account for differences between precincts while pooling information within larger groups.
One version proved too computationally demanding, another failed its final numerical check, so the branch never reached a substantive run
- **Expected-value ranges for individual UIKs.** A range was constructed for a precinct that could serve as a reference for prediction quality based on similar precincts.
This approach passed its check, but remained a diagnostic rather than a recalculation scenario. Even if a precinct falls outside its expected range, the method does not say what the alternative value should be or exactly what should replace the observed result
- **Reports of possible violations.** These were used as documentary context. They could not reliably be turned into large-scale labels for individual UIKs, and the absence of a report cannot be treated as evidence of a “clean” precinct

</details>

## What could be studied next?

The study deliberately did not enumerate every possible variant of each model.

For D, other focal parties could be tested separately, or a new symmetric version for all parties could be developed. That would be a different model, not a simple continuation of the current calculation.

The number of components could be changed for the one-dimensional and two-dimensional models.
For the two-dimensional model, component shape, coordinate scaling or the way UIK size is taken into account could also be varied.
For example, larger precincts could receive more weight in proportion to their number of registered voters.
The model would then describe the distribution of voters more strongly, rather than the distribution of precincts themselves. This changes the question itself, not just a technical setting.

For the Important Stories reconstruction, other ways of handling positive and negative deviations and a different denominator recalculation could be studied.

For Cedar, one could try to formalize the qualitative regional applicability rules that remain partly a manual choice in the public description.

Combinations of several changes could also be tested — for example, changing the data version, excluding a region and changing a model setting at the same time.
This is computationally possible, but sharply increases the number of variants.

All these directions emerged before we saw what the corresponding calculations would produce.
They are not outside the current work because they produced inconvenient numbers. Each such step expands the set of models, requires new rules to be fixed separately and a new run to be performed. In other words, I would be doing this for another year.

A separate question remains about models that directly use statistical unusualness (anomalies) to choose where to recalculate.
The formulation considered here stopped at requirements analysis and mathematical counterexamples, and therefore reached neither model testing nor real data. But this, too, is a potentially interesting topic for a new study.

Technical materials, settings, checksums, results and the full list of sources used are available in the [research repository](https://github.com/MaximTar/election-2026) and the [Reproducibility materials v1 release](https://github.com/MaximTar/election-2026/releases/tag/reproducibility-v1).
Third-party raw data snapshots are not separately republished. Their sources and exact SHA256 hashes are provided.
