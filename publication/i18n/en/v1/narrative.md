# Between the data and the conclusion

**Translation note.** This English version was translated from the original Russian with OpenAI models and checked for semantic consistency. The Russian release remains the authoritative version. Translation errors are still possible.

I came across a [Novaya Gazeta Europe article](https://novayagazeta.eu/articles/2026/09/24/nastoiashchii-rezultat-er-dorisovki-za-oppozitsiiu-i-skorostnye-sultanaty) that estimated United Russia's result in paper voting at about 34%.

My first reaction was a fairly simple question: **where did that number come from?**

In the study's primary paper-precinct dataset, the observed share was about 58.7%.
Other publications gave estimates of about 25% and 35%. If you look only at the final percentages, it is natural to see them as competing estimates of the same quantity.

That led to the idea of reproducing several approaches on one dataset and seeing where the differences came from.

As the work progressed, it became clear that comparing all these numbers as candidates for one “correct” result is usually inappropriate.
It proved much more interesting to understand **which decisions have to be made before a table of results can yield any alternative percentage at all**.

Which precincts should be compared? What should count as normal? Should all precincts be recalculated, or only some? Should the result be recalculated for one party or all of them at once? What happens if the model cannot say anything about a particular region? What should even count as the model's output?

To a large extent, it is these questions that give rise to the final number.

Let me say at the outset: I am not trying to establish the “true result” of the election.
Nor am I trying to use these models either to prove the absence of violations or to establish their scale.

This is a study of a narrower question: **what happens when different calculation rules are applied to the same data?**

## What if we compare similar precincts?

The study's primary dataset contains data from 87 736 paper-voting precinct election commissions (UIKs) in 84 regions. Remote electronic voting and overseas precincts are kept separately.

Let's start with a fairly intuitive construction. For a given precinct, we can try to find similar precincts within the same territorial election commission (TIK). Then ask:
**what would happen if the selected precinct's result were more like this group's results?**

Three scenarios emerged from this idea.

A retains the total number of valid votes, but moves their distribution among parties towards the comparison group.

B retains party proportions, but changes the overall scale of the related counts.

C combines both changes.

And the first limitation appeared immediately.

It is not enough to say “let's compare similar precincts”. We have to define in advance what “similar” means.

In the default version, the targets were precincts in the top quarter of their TIK by the ratio of ballots issued to registered voters.
The comparison group also came from the same TIK, but from a lower part of the distribution. The difference in precinct size was also restricted, and at least five suitable neighbors were required.

Of the 87 736 UIKs, the comparison specified by the rules could ultimately be constructed for only 5 391.
The scenario therefore changes nothing at the other precincts.

The result across the whole dataset consequently shifts relatively little.

This brings us back to the original publication.

If an approach like this barely moves the nationwide result, where do the published 25–35% come from?

## One party versus everyone else

Many such estimates are connected with another idea. In simplified form, it works like this:
Take one party's votes and the votes for all the others.
Look at how they are distributed by participation level.
Then select some lower part of the distribution as a reference.
If this area has a certain number of votes for the selected party for every hundred votes for the others, we can extend that ratio to precincts with higher participation and see how far the observed curve differs from it.

This idea is associated with the work of Dmitry Kobak, Sergey Shpilkin and Maxim Pshenichnikov, and exists in many implementations.

But the general idea is not enough to produce a single number.
Each particular implementation still has to make several more decisions.
So **“Shpilkin's method” does not, by itself, define the calculation**.

Which part of the distribution should serve as the reference?

Should the whole country be treated as one curve, or should regions be calculated separately?

Should the calculation use one interval or several?

Should negative deviations be retained?

Which precincts should be included at all?

All these decisions have to be made before the number appears.

### Important Stories

For the 2026 election, [Important Stories](https://istories.media/stories/2026/09/22/bolee-18-iz-30-mln-bumazhnikh-golosov-za-edinuyu-rossiyu-mogli-bit-sfalsifitsirovani/) specifies a participation level of 20–29% as the reference area and publishes a result of about 35%.

Its input data differ from this study's dataset: it is an earlier snapshot, Moscow is excluded, and electronic voting is not counted. In addition, not all the calculation details could be reconstructed from the publication.

The task was therefore not to find a formula that would necessarily give the same 35%.
Instead, one specific implementation of the published idea was fixed in advance.
On the study's primary dataset, it gave 38.00%.

But something else proved more interesting.
Before viewing the results, I specified another 14 alternative reference ranges.
The answers ranged from **36.33% to 43.64%**.

Even within one general construction, the choice of reference area thus produced a spread of more than seven percentage points.
And different areas drew on very different numbers of precincts: from 141 to 17 501.

This is not a confidence interval. We cannot say: “the true result lies between 36 and 44”.
It merely demonstrates how much the result of this construction depends on one preselected rule.

### Cedar

The [Cedar](https://github.com/Cedar-Russia/electoral_statistics) project's code is publicly available.

It uses one narrow interval as its reference, rather than a broad range.

In the Cedar adaptation fixed in advance for this study, the automatic procedure selected an interval between 43% and 44%.

The result was **41.74%**.

Cedar is not calculated on the whole primary dataset: this adaptation includes 71 438 of the 87 736 UIKs.

But it is easy to make a very serious mistake here. The 41.74% is **not the party's result**.

Imagine that a party received 100 votes, while the other counted ballots amounted to 200.
Using the ratio in the selected reference interval, the model says: given these 200 other ballots, we would expect, for example, 58 votes for the party.
The actual count was 100.
The difference is 42.
Dividing it by the party's actual 100 votes gives 42%.
That is roughly what the Cedar measure means.

To make the difference between the two kinds of percentage clearer, we can take another step.
Originally, the party had 100 out of 300, or 33.3%.
Replacing 100 with the model's 58 and leaving the other 200 unchanged gives 58 out of 258, or about 22.5%.
This is now the party's share of all counted ballots, including invalid ones.
But **22.5% and 42% are two different measures**, even though both are expressed as percentages.

Cedar's main output is the residual measure: the size of the model residual relative to the party's observed votes.
This example shows particularly clearly why it is dangerous to put several percentages in one column and ask which is correct.
They may not even measure the same quantity.

## What if we put together another version of this idea?

We can define yet another variant of the idea. We will call it D.
It also compares the selected party with the sum of the others, but the calculation is performed separately within regions or TIKs, and the proportion is estimated from several intervals in the lower part of the distribution.

Importantly, D is not an “improved Shpilkin method” or a “corrected Cedar”.
It is simply another scenario.

Five preselected D variants gave roughly **52–56%** for United Russia. The default version is 53.25%.
That is much higher than the published 25–35%.

But the discrepancy alone says nothing about the quality of the estimate.
D uses different geography, a different reference area, a different way of estimating the proportion and different rules for what happens where the calculation is undefined.

So, again, it is not only the number that changes.
The question itself changes.

## Novaya Gazeta Europe

So far, we have discussed constructions that define alternative values or an expected vote curve in one way or another.
But the Novaya Gazeta Europe publication also has another approach.
Instead of recalculating votes, the authors examine the shape of the distribution of results.

Imagine a histogram: the horizontal axis shows the party's result at a precinct, while the height shows how many party votes come from precincts with that result.
We can try to describe the shape of this histogram with several Gaussians.

Novaya Gazeta Europe's publication uses three components with centers roughly around 33%, 60% and 93%.
The authors call the component with the lowest center the “honest core”.
In our reconstruction of the model, the center of that component was **35.23%**.

This brings us to one of the main subtleties of the entire study.
**First the model calculates something. Then we decide how to interpret it.**

The direct statistical result here looks like this:

> a component with a center around 35% is identified in the distribution.

A substantive step can then follow:

> if we treat this component as an “honest core”, its center can be interpreted as an estimate of the party's result without fraud.

That is how Novaya Gazeta Europe's authors interpret a similar result.

I am not claiming that this interpretation is right or wrong.

But it is still a separate step.

The mathematical fit itself does not establish why this component arose or whether its existence must specifically be associated with fraud.

That is a substantive explanation of the statistical structure of the data.

## What if we look in two dimensions?

We can take each UIK not as one number, but as a point with two coordinates:

- participation level
- party result

The model then tries to divide the whole point cloud into several components.

In the reconstruction, the selected component's center is roughly **34.37% on the party-result axis**, and at a membership threshold above 50%, 18 904 UIKs are assigned to it.

But here, too, the number from 0 to 100% with which the model expresses a precinct's component membership cannot be read as the probability that the precinct is “honest”.

It is only the probability of belonging to a mathematical component **within the selected model**.

The substantive meaning of that component again appears at the next step.

## Anomalies

Before all these scenarios, the project searched for statistically unusual structures (or anomalies).
For example, an association between participation level and party result.

The next step seems natural: if we see unusual precincts, use that signal to choose where to recalculate.

The problem arises if the same result is used both to select precincts and then to test the resulting conclusion.
Suppose a high party result helps a precinct enter the “anomalous” group.
An alternative calculation is then constructed specifically for that group, moving its result towards a lower comparison group.
The reduction is then partly built into the selection rule itself.
After that, the resulting reduction cannot be used as independent confirmation that the original high result was indeed distorted.

The formulation itself was therefore examined separately using two artificial examples with a known data construction.
It turned out that ordinary heterogeneity and a deliberately introduced change can produce identical observations.
Such data alone cannot guarantee that we distinguish these cases while simultaneously requiring the rule not to create an unnecessary adjustment in the first and to recover the original state in the second.

This branch was ultimately stopped before model implementation or application to real data.

Not every way of obtaining some result is worth applying to real data merely because it technically works.

## Are there any conclusions?

Before starting, I thought the data would prove to be the main source of discrepancies.

Different sources do have discrepancies. Data are updated. Individual protocols can change.
The study therefore used several input-dataset variants stored in advance.

But in many of the constructions tested, differences between these data versions were smaller than differences caused by changing the model's own rules.

For example, in the reconstruction of the Important Stories approach, changing the data version moved the default result by about half a percentage point.
Changing the reference area moved it by more than seven.

For Cedar, differences between source versions were very small relative to its enormous sensitivity to the choice of a single reference interval. In the tested grid, the model residual even changed sign.

This does not mean that data quality is unimportant.

Still less does it mean that the model always matters more than the data.

The conclusion can therefore be put this way: **some of what looks like a difference between “estimates of the result” is actually a difference between the questions being formulated.**

But there is another conclusion that is easy to lose in discussions of fixing rules in advance.
**Choosing a rule in advance is not enough. We also need to understand why that particular rule was chosen.**

Fixing it in advance protects against adjusting the method after we have seen the result.
But it does not, by itself, justify a particular threshold, reference range or comparison method.
A rule may have different motivations: it may reproduce a choice from a published method, follow from the model's own structure, or be one of the predeclared variants for testing sensitivity.
If there is no explanation for the choice, that, too, is important information about the study.

## So which percentage is correct?

After all this, the question already seems a little strange.

25%, 34%, 38%, 42%, 53% and 58% cannot simply be placed on one scale.

One number may be an alternative party share.

Another may be the model residual as a fraction of the party's observed votes.

A third may be a statistical component center.

A fourth may be the result of a scenario that changes only a small fraction of precincts and leaves the others as observed.

And even when two methods give almost identical percentages, that still does not mean they have independently confirmed each other.

They may use related data, similar assumptions or calculate different quantities altogether.

A mathematical component center and the statement “this is an estimate of the result without fraud” are not the same thing.

Interpretation lies between them.

It may be reasonable and well justified. But it is useful to see it separately from the calculation itself.

We can ultimately formulate five questions to ask whenever you see impressive numbers from a complex model:

**What exactly was calculated?**

**On which data?**

**Why were these particular rules chosen?**

**How is this number interpreted?**

**How much does it change if the selected rules change?**

The study was carried out with assistance from OpenAI models.
They helped write code, perform checks, find sources and examine results.
The research questions and key decisions about what exactly to calculate, how to calculate it and which variants to test remained with me.

---

The full technical version, with all rules, limitations, tables and checks: [article](https://election-2026-explorer.max-tar.chatgpt.site/article).

The interactive Scenario Explorer, where you can switch between precomputed variants: [project site](https://election-2026-explorer.max-tar.chatgpt.site/).

Code, settings, checksums, frozen results and reproduction materials: [project repository](https://github.com/MaximTar/election-2026) and [Reproducibility materials v1](https://github.com/MaximTar/election-2026/releases/tag/reproducibility-v1).

Third-party raw data snapshots are not separately republished. Their sources and exact checksums are retained.
