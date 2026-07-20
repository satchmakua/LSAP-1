# LSAP-1 — reliability report

segments: 30   raters: claude-haiku-4-5, claude-opus-4-8   axes_version: 3
rater pairs: claude-haiku-4-5 vs claude-opus-4-8   segments in PCA: 30

## Per-axis agreement, averaged across rater pairs (scalar: within-1 rate; forced-choice: exact-match)
  L1  Lexical Complexity         within1=0.30 spearman=+0.75 wkappa=+0.30 |d|=1.83 conf=4.2
  L2  Syntactic Depth            within1=0.90 spearman=+0.83 wkappa=+0.81 |d|=0.67 conf=4.33
  L3  Semantic Density           within1=0.83 spearman=+0.86 wkappa=+0.59 |d|=1.13 conf=3.87
  L4  Imagery Mode               within1=0.83 spearman=+0.55 wkappa=+0.54 |d|=0.90 conf=4.0
  L5  Repetition Pattern         within1=0.93 spearman=+0.55 wkappa=+0.57 |d|=0.77 conf=4.35
  N1  Event Density              within1=0.73 spearman=+0.73 wkappa=+0.64 |d|=0.93 conf=4.03
  N2  Structural Linearity       within1=0.97 spearman=+0.63 wkappa=+0.88 |d|=0.50 conf=4.3
  N3  Causal Clarity             within1=0.40 spearman=+0.38 wkappa=+0.17 |d|=1.73 conf=3.95
  N4  Temporal Behavior          within1=0.83 spearman=+0.63 wkappa=+0.73 |d|=0.63 conf=3.88
  N5  Plot Centrality            within1=0.80 spearman=+0.53 wkappa=+0.64 |d|=0.93 conf=4.23
  C1  Narrative Distance         within1=0.83 spearman=+0.79 wkappa=+0.81 |d|=0.67 conf=4.2
  C2  Subject Stability          within1=0.90 spearman=+0.56 wkappa=+0.80 |d|=0.70 conf=4.27
  C3  Cognitive Transparency     within1=0.90 spearman=+0.84 wkappa=+0.86 |d|=0.73 conf=4.27
  C4  Polyphony                  within1=1.00 spearman=+0.64 wkappa=+0.81 |d|=0.43 conf=4.28
  C5  Interior/Exterior Ratio    within1=0.77 spearman=+0.86 wkappa=+0.76 |d|=1.07 conf=4.13
  P1  Ontological Stability      within1=0.90 spearman=+0.81 wkappa=+0.92 |d|=0.43 conf=4.53
  P2  Epistemic Certainty        within1=0.90 spearman=+0.87 wkappa=+0.86 |d|=0.67 conf=3.97
  P3  Moral-Structure Clarity    within1=0.83 spearman=+0.48 wkappa=+0.43 |d|=0.80 conf=3.47
  P4  Meaning Structure          within1=0.70 spearman=+0.68 wkappa=+0.62 |d|=1.10 conf=3.68
  P5  Agency Model               within1=0.70 spearman=+0.73 wkappa=+0.61 |d|=1.00 conf=3.72
  A1  Valence                    within1=1.00 spearman=+0.85 wkappa=+0.90 |d|=0.47 conf=4.1
  A2  Emotional Volatility       within1=0.87 spearman=+0.72 wkappa=+0.59 |d|=0.77 conf=3.82
  A3  Dominant Affect            exact=0.67 kappa=+0.57 conf=3.98
  A4  Intensity Curve            within1=0.90 spearman=+0.86 wkappa=+0.81 |d|=0.57 conf=3.88
  A5  Resolution Type            exact=0.73 kappa=+0.54 conf=3.85
  S1  Rhythm Regularity          within1=0.87 spearman=+0.54 wkappa=+0.44 |d|=0.80 conf=3.72
  S2  Sentence-Length Variance   within1=0.87 spearman=+0.58 wkappa=+0.37 |d|=0.77 conf=4.13
  S3  Voice Dominance            within1=0.90 spearman=+0.62 wkappa=+0.63 |d|=0.83 conf=4.33
  S4  Figurative Density         within1=0.97 spearman=+0.92 wkappa=+0.91 |d|=0.60 conf=4.33
  S5  Aesthetic Register         exact=0.83 kappa=+0.71 conf=4.18

## Reliable axes (27): L2, L3, L4, L5, N1, N2, N4, N5, C1, C2, C3, C4, C5, P1, P2, P3, P4, P5, A1, A2, A4, A5, S1, S2, S3, S4, S5
## Ambiguous axes (2): L1, N3

## Redundant axis pairs (|r| >= 0.8)
  C1 ~ C3  r=+0.94
  N2 ~ N4  r=+0.93
  C3 ~ C5  r=+0.92
  C1 ~ C5  r=+0.91
  P1 ~ P2  r=+0.86
  N3 ~ P2  r=+0.83
  L2 ~ L3  r=+0.82
  L2 ~ S4  r=+0.82
  N5 ~ C5  r=+0.81
  L1 ~ L2  r=+0.81
  C5 ~ S4  r=+0.81

## PCA over scalar axes
  explained variance (top): [0.4373, 0.1187, 0.0995, 0.0788, 0.0578, 0.0504, 0.0364, 0.0287]
  cumulative (top): [0.4373, 0.556, 0.6555, 0.7344, 0.7922, 0.8426, 0.879, 0.9077]
  components for 80% / 90%: 6 / 8
  top-loading axes per component:
    PC1: C5(+0.25), S4(+0.24), L2(+0.24), N3(+0.24), C2(+0.23)
    PC2: P4(+0.45), P3(+0.34), P2(+0.28), A4(-0.25), S2(-0.24)
    PC3: N1(+0.36), A2(+0.35), L3(-0.32), S1(-0.30), A1(-0.28)
    PC4: C4(+0.42), L1(-0.37), A4(-0.34), N5(+0.31), N1(-0.27)
    PC5: S1(+0.60), L4(-0.38), L5(+0.29), S3(+0.27), A1(-0.23)
    PC6: N2(+0.42), N5(-0.37), P5(-0.35), C4(+0.35), N4(+0.33)

## Twin-pair consistency (mean |d| over scalar axes)
  twin pairs: 4   twin mean: 0.565   all-pairs mean: 1.483

## Before/after re-anchoring — axes_version 1 vs 3
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
