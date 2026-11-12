# Reliability notes

What the rated corpus currently supports, how each number is computed, and two
corrections to results I had already published. The live figures are regenerated into
[`reliability/report.md`](../reliability/report.md) by
`python -m lsap.coordinates.reliability`; this note explains them.

Nothing here is a claim about ground truth. "Reliable" means two raters applying the same
manual land close together; it does not mean either is right (Charter P1/P2).

## Where things stand (n=100, anchors version 3)

Corpus: 100 segments — 85 written to structural briefs by a model, 15 public-domain
passages as a control. Raters: `claude-opus-4-8` and `claude-haiku-4-5`. No human rater
yet; the tooling for one is in place (see *Human scoring* below).

| | n=30 pilot | n=100 |
|---|---|---|
| PC1 share of variance | 44.8% | **33.8%** |
| Five factors explain | 79.4% | **70.9%** |
| C6 residual | 20.6% | **29.1%** |
| Components needed for 80% | 6 | **8** |
| Split-half loading stability (mean abs. r) | 0.505 | **0.679** |

- **26 of 30 axes** clear the reliability bar (within-1 ≥ 0.70 for scalar axes,
  exact-match ≥ 0.70 for forced-choice, mean confidence ≥ 3). The four that do not:
  **L1** Lexical Complexity (0.52), **A3** Dominant Affect (0.53), **N3** Causal Clarity
  (0.55), **N5** Plot Centrality (0.66).
- **The Consciousness axes still collapse** into one interiority factor
  (C1~C3 r=0.91, C3~C5 0.90, C1~C5 0.85).
- **Twin pairs stay close.** Each of the 26 twin-pair members has its twin within the
  top 5 of the 99 other segments (median rank 1, mean 1.9); 15 of 26 have it as the single
  nearest neighbour.

The pilot's tidy five-factor picture was substantially an artifact of n=30: it explains
less at n=100 and needs more components. What improved is *reproducibility* — the same
loadings come back from two random halves far more often (PC1 0.87, PC2 0.84) — so the
smaller corpus was fitting noise it had no way to detect.

## Corrections (2026-11-11)

Two results I published from the M5 and M6 runs were wrong. Both came from the analysis
code, not the ratings, and both are fixed with regression tests.

### 1. Spearman correlations ignored ties

Rank agreement was computed by ranking with `argsort(argsort(x))`, which hands tied values
arbitrary distinct ranks. Scores on a 1–7 scale across 30 or 100 segments are almost
entirely ties, so this was not a rounding matter: per-axis rho was off by up to **0.17**
(mean 0.05), usually too low. Ranks now share their average, the standard convention.

What changes in the M5 account of the two re-anchored axes, over the same 30 segments:

| | anchors v1 | v2 | v3 |
|---|---|---|---|
| **L1** rho (published as "held ~0.75") | 0.86 | 0.71 | 0.72 |
| L1 within-1 | 0.40 | 0.37 | 0.30 |
| L1 offset (Haiku − Opus) | +1.63 | +1.83 | +1.83 |
| **L3** rho | 0.81 | 0.78 | 0.88 |
| L3 within-1 | 0.40 | 0.67 | 0.83 |
| **N3** rho (anchors never changed) | 0.60 | 0.54 | 0.45 |

The diagnosis that motivated re-anchoring — the raters rank together but calibrate
differently — was right, and stronger than reported (L1 0.86, L3 0.81). The conclusion
about L1 gets worse, not better: re-anchoring did not merely fail to close the offset, it
**lowered rank agreement** (0.86 → 0.72) while the offset stayed frozen. The counting
anchors made the two raters order segments less alike than the original vague ones did.
L3 is a clean success on both measures. N3's drift, which I had put down partly to noise,
shows up in rank order too.

### 2. "The factors are not a generator artifact" did not follow

I reported that the public-domain passages "load the same structure (loading match
|r| 0.95–0.999)". That compared loadings fitted on the 85 model-written segments with
loadings fitted on all 100. Eighty-five of those hundred rows are the same rows, so a
close match was guaranteed whatever the other fifteen looked like. The test could not
fail, and it has been removed.

The replacement is out of sample. Each of 200 seeded splits holds out 15 model-written
segments, fits the scaler and five factors on the other 70, and measures the share of
variance those factors capture in (a) the 15 held-out model-written segments and (b) the
15 public-domain passages, under the identical fit:

| Variance captured by five factors fitted on model-written prose | mean | 5th–95th pct |
|---|---|---|
| held-out model-written segments | **0.661** | 0.591–0.723 |
| public-domain passages | **0.521** | 0.489–0.562 |

The public-domain passages come out lower in 199 of the 200 splits. Part of the 0.14 gap
is extremity: passages near the centroid are proportionally noisier and captured less
(r=+0.42 between extremity and capture), and the public-domain set is milder than a corpus
written to exaggerate its briefs. Restricting the held-out model segments to the
public-domain set's extremity range leaves a gap of **0.11**, concentrated in the mildest
and the most extreme passages and absent in between. It is not one outlier: 12 of the 15
fall below the model-written median, and dropping the lowest (*Bartleby*) moves the pooled
figure only from 0.52 to 0.53.

So the corrected finding is the opposite of the published one: **the factors describe
prose no model wrote measurably less well than they describe generated prose.** The
structure is partly a property of the generated corpus. The residual is about a third for
generated text and nearer a half for the public-domain control. Fifteen passages is a
small sample and this is indicative, but it is the result the data gives, and it argues
for more non-model prose before the factors are trusted outside generated text.

The per-axis level differences reported alongside it stand: public-domain passages score
lower on Valence (−0.99), Repetition (−0.79), and Event Density (−0.77), and higher on
Cognitive Transparency (+0.82) and Interior/Exterior Ratio (+0.63).

## How the numbers are computed

- **Anchor cohorts are never pooled.** Every rating records the `axes_version` it was
  scored under. Ratings are append-only; selection is newest-wins per rater and segment
  within one version.
- **Agreement is per rater pair, over the segments both raters scored.** The per-axis
  headline is the mean across pairs weighted by each pair's n, so a pair that shares 8
  segments cannot outvote one that shares 100.
- **The consensus comes from a panel.** Only raters covering at least 90% of the segments
  are averaged into the consensus that feeds the correlation matrix, the PCA, and the
  fitted projection. A rater with partial coverage is compared against the panel, never
  pooled into it — otherwise a segment's position would depend on who happened to rate
  it. The panel is recorded in `coordinates/model.json`.
- **Before/after comparisons are like-for-like**: the same segments and the same raters
  in both cohorts. Without that, growing the corpus looks like an anchor effect.
- **Split-half stability**: PCA on two random halves, components matched by absolute
  correlation of loadings (sign and order are arbitrary), averaged over 20 seeded splits.
- **Twin rank**: for each member of a twin pair, the rank of its twin among all other
  segments by distance in the fitted space. A rank stays comparable as the corpus grows;
  a nearest-neighbour hit rate does not, because a denser space adds competitors.
- Every random procedure is seeded. Re-running reproduces the report.

## Human scoring

A person can score through the same contract as the model raters
(`POST /api/rate/manual`, stored as `human:<name>`). Scoring is **blind**: the Rater
Studio lists segments under opaque codes rather than ids and never shows a model score,
because the model raters see only the text — an id such as `baroque-memory`, or an
author's name, would prime the judgments being measured. The first twelve segments
offered were fixed in brief space before any human rating existed.

Once a human has scored at least eight segments the report gains human↔model agreement
per axis and lists the axes where they diverge most. That divergence is data, and is not
to be tuned away.

## Open questions

- **L1 Lexical Complexity.** Two anchor revisions are spent and the stop rule applies, so
  no further retuning. Given that the revisions lowered rank agreement, the live options
  are restoring the original anchors, splitting the axis (technical rarity vs
  literary-register elevation), or retiring it toward L2 and L3, with which it correlates
  at about 0.70.
- **A3 Dominant Affect** (0.53 exact-match) is the weakest forced-choice axis and has
  never had an anchor revision. The comic and warm registers added in M6 gave the raters
  more to disagree about.
- **N3 Causal Clarity** degrades under re-measurement with unchanged anchors.
- **More non-model prose.** Fifteen public-domain passages were enough to show the
  factors fit them less well; they are not enough to say how much less.
