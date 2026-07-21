# LSAP-1 — reliability report

segments: 100   raters: claude-haiku-4-5, claude-opus-4-8   axes_version: 3
rater pairs: claude-haiku-4-5 vs claude-opus-4-8   segments in PCA: 100

## Per-axis agreement, averaged across rater pairs (scalar: within-1 rate; forced-choice: exact-match)
  L1  Lexical Complexity         within1=0.52 spearman=+0.56 wkappa=+0.31 |d|=1.47 conf=4.11
  L2  Syntactic Depth            within1=0.89 spearman=+0.75 wkappa=+0.77 |d|=0.67 conf=4.14
  L3  Semantic Density           within1=0.87 spearman=+0.66 wkappa=+0.55 |d|=0.89 conf=3.77
  L4  Imagery Mode               within1=0.82 spearman=+0.40 wkappa=+0.49 |d|=0.92 conf=3.89
  L5  Repetition Pattern         within1=0.94 spearman=+0.61 wkappa=+0.57 |d|=0.70 conf=4.26
  N1  Event Density              within1=0.75 spearman=+0.80 wkappa=+0.68 |d|=0.90 conf=3.97
  N2  Structural Linearity       within1=0.88 spearman=+0.55 wkappa=+0.72 |d|=0.71 conf=4.19
  N3  Causal Clarity             within1=0.55 spearman=+0.38 wkappa=+0.22 |d|=1.38 conf=3.92
  N4  Temporal Behavior          within1=0.83 spearman=+0.64 wkappa=+0.70 |d|=0.79 conf=3.85
  N5  Plot Centrality            within1=0.66 spearman=+0.36 wkappa=+0.40 |d|=1.20 conf=4.03
  C1  Narrative Distance         within1=0.81 spearman=+0.71 wkappa=+0.69 |d|=0.82 conf=4.01
  C2  Subject Stability          within1=0.86 spearman=+0.39 wkappa=+0.58 |d|=0.71 conf=4.21
  C3  Cognitive Transparency     within1=0.82 spearman=+0.82 wkappa=+0.76 |d|=0.88 conf=4.04
  C4  Polyphony                  within1=0.94 spearman=+0.67 wkappa=+0.83 |d|=0.66 conf=4.16
  C5  Interior/Exterior Ratio    within1=0.73 spearman=+0.73 wkappa=+0.66 |d|=1.15 conf=3.96
  P1  Ontological Stability      within1=0.96 spearman=+0.77 wkappa=+0.90 |d|=0.30 conf=4.58
  P2  Epistemic Certainty        within1=0.93 spearman=+0.74 wkappa=+0.85 |d|=0.50 conf=3.87
  P3  Moral-Structure Clarity    within1=0.85 spearman=+0.50 wkappa=+0.48 |d|=0.72 conf=3.54
  P4  Meaning Structure          within1=0.75 spearman=+0.66 wkappa=+0.58 |d|=1.03 conf=3.69
  P5  Agency Model               within1=0.75 spearman=+0.57 wkappa=+0.56 |d|=1.01 conf=3.62
  A1  Valence                    within1=0.97 spearman=+0.90 wkappa=+0.90 |d|=0.54 conf=4.01
  A2  Emotional Volatility       within1=0.88 spearman=+0.62 wkappa=+0.59 |d|=0.65 conf=3.69
  A3  Dominant Affect            exact=0.53 kappa=+0.46 conf=3.9
  A4  Intensity Curve            within1=0.89 spearman=+0.69 wkappa=+0.72 |d|=0.61 conf=3.83
  A5  Resolution Type            exact=0.84 kappa=+0.74 conf=3.81
  S1  Rhythm Regularity          within1=0.91 spearman=+0.66 wkappa=+0.63 |d|=0.63 conf=3.71
  S2  Sentence-Length Variance   within1=0.87 spearman=+0.46 wkappa=+0.40 |d|=0.80 conf=4.12
  S3  Voice Dominance            within1=0.87 spearman=+0.50 wkappa=+0.48 |d|=0.77 conf=4.32
  S4  Figurative Density         within1=0.84 spearman=+0.79 wkappa=+0.74 |d|=0.79 conf=4.03
  S5  Aesthetic Register         exact=0.79 kappa=+0.60 conf=4.02

## Reliable axes (26): L2, L3, L4, L5, N1, N2, N4, C1, C2, C3, C4, C5, P1, P2, P3, P4, P5, A1, A2, A4, A5, S1, S2, S3, S4, S5
## Ambiguous axes (0): —

## Redundant axis pairs (|r| >= 0.8)
  C1 ~ C3  r=+0.91
  C3 ~ C5  r=+0.90
  C1 ~ C5  r=+0.85
  N5 ~ C5  r=+0.81
  L2 ~ L3  r=+0.80

## PCA over scalar axes
  explained variance (top): [0.3376, 0.15, 0.0885, 0.0729, 0.0603, 0.052, 0.0374, 0.0276]
  cumulative (top): [0.3376, 0.4876, 0.5761, 0.649, 0.7093, 0.7613, 0.7986, 0.8263]
  components for 80% / 90%: 8 / 12
  top-loading axes per component:
    PC1: C5(+0.27), L2(+0.24), C2(+0.24), C3(+0.24), C1(+0.23)
    PC2: P4(+0.37), A4(-0.31), A1(-0.30), P2(+0.30), S4(-0.27)
    PC3: A2(+0.36), L1(-0.35), L3(-0.35), S1(-0.34), C3(+0.32)
    PC4: N1(+0.48), A2(+0.37), A4(+0.34), L5(+0.27), C5(-0.26)
    PC5: C4(+0.53), P3(-0.38), N4(+0.34), N2(+0.30), A1(+0.30)
    PC6: L5(+0.47), S1(+0.31), N5(+0.31), L1(-0.31), L2(-0.28)

## Split-half stability (PCA loadings, 20 seeded splits of 50+50)
  |r| per component: [0.867, 0.842, 0.612, 0.586, 0.486]   mean: 0.679

## Origin check — model (n=85) vs other origins (n=15; indicative only at this n)
  loading match |r| (model-only fit vs all-fit): [0.998, 0.999, 0.991, 0.949, 0.975]
  largest per-axis consensus offsets (minority − majority): A1(-0.99), C3(+0.82), L5(-0.79), N1(-0.77), C5(+0.63)

## Twin-pair consistency (mean |d| over scalar axes)
  twin pairs: 13   twin mean: 0.527   all-pairs mean: 1.315

## Before/after re-anchoring — axes_version 1 vs 3
   Like-for-like: the 30 segments rated under BOTH cohorts,
   so corpus growth cannot masquerade as an anchor effect.
   (per-axis primary agreement: within-1 for scalar, exact-match for forced-choice)
   axis                            v1     v3     delta
   L1  Lexical Complexity          0.40   0.30   -0.10  <-- re-anchored
   L2  Syntactic Depth             0.90   0.90   +0.00
   L3  Semantic Density            0.40   0.83   +0.43  <-- re-anchored
   L4  Imagery Mode                0.80   0.83   +0.03
   L5  Repetition Pattern          0.87   0.93   +0.07
   N1  Event Density               0.73   0.73   +0.00
   N2  Structural Linearity        0.97   0.97   +0.00
   N3  Causal Clarity              0.73   0.40   -0.33
   N4  Temporal Behavior           0.90   0.83   -0.07
   N5  Plot Centrality             0.80   0.80   +0.00
   C1  Narrative Distance          0.83   0.83   +0.00
   C2  Subject Stability           0.97   0.90   -0.07
   C3  Cognitive Transparency      0.90   0.90   +0.00
   C4  Polyphony                   1.00   1.00   +0.00
   C5  Interior/Exterior Ratio     0.83   0.77   -0.07
   P1  Ontological Stability       0.87   0.90   +0.03
   P2  Epistemic Certainty         0.87   0.90   +0.03
   P3  Moral-Structure Clarity     0.80   0.83   +0.03
   P4  Meaning Structure           0.80   0.70   -0.10
   P5  Agency Model                0.70   0.70   +0.00
   A1  Valence                     1.00   1.00   +0.00
   A2  Emotional Volatility        0.73   0.87   +0.13
   A3  Dominant Affect             0.67   0.67   +0.00
   A4  Intensity Curve             0.97   0.90   -0.07
   A5  Resolution Type             0.67   0.73   +0.07
   S1  Rhythm Regularity           0.83   0.87   +0.03
   S2  Sentence-Length Variance    0.90   0.87   -0.03
   S3  Voice Dominance             0.77   0.90   +0.13
   S4  Figurative Density          0.73   0.97   +0.23
   S5  Aesthetic Register          0.80   0.83   +0.03
   regressions (> 0.10 drop): N3
