# LSAP-1 — M2 reliability report

segments: 30   raters: claude-haiku-4-5, claude-opus-4-8

## Per-axis inter-rater agreement (scalar: within-1 rate; forced-choice: exact-match)
  L1  Lexical Complexity         within1=0.40 spearman=+0.76 wkappa=+0.41 |d|=1.63 conf=4.38
  L2  Syntactic Depth            within1=0.90 spearman=+0.83 wkappa=+0.80 |d|=0.77 conf=4.47
  L3  Semantic Density           within1=0.40 spearman=+0.74 wkappa=+0.47 |d|=1.60 conf=4.17
  L4  Imagery Mode               within1=0.80 spearman=+0.66 wkappa=+0.71 |d|=0.83 conf=4.07
  L5  Repetition Pattern         within1=0.87 spearman=+0.70 wkappa=+0.55 |d|=0.77 conf=4.45
  N1  Event Density              within1=0.73 spearman=+0.79 wkappa=+0.69 |d|=0.93 conf=4.22
  N2  Structural Linearity       within1=0.97 spearman=+0.77 wkappa=+0.85 |d|=0.60 conf=4.35
  N3  Causal Clarity             within1=0.73 spearman=+0.44 wkappa=+0.51 |d|=0.83 conf=4.0
  N4  Temporal Behavior          within1=0.90 spearman=+0.72 wkappa=+0.73 |d|=0.83 conf=4.0
  N5  Plot Centrality            within1=0.80 spearman=+0.58 wkappa=+0.72 |d|=0.83 conf=4.4
  C1  Narrative Distance         within1=0.83 spearman=+0.77 wkappa=+0.73 |d|=0.80 conf=4.4
  C2  Subject Stability          within1=0.97 spearman=+0.69 wkappa=+0.89 |d|=0.57 conf=4.33
  C3  Cognitive Transparency     within1=0.90 spearman=+0.93 wkappa=+0.83 |d|=0.80 conf=4.35
  C4  Polyphony                  within1=1.00 spearman=+0.67 wkappa=+0.83 |d|=0.37 conf=4.25
  C5  Interior/Exterior Ratio    within1=0.83 spearman=+0.75 wkappa=+0.77 |d|=1.00 conf=4.25
  P1  Ontological Stability      within1=0.87 spearman=+0.79 wkappa=+0.84 |d|=0.70 conf=4.53
  P2  Epistemic Certainty        within1=0.87 spearman=+0.91 wkappa=+0.86 |d|=0.70 conf=4.0
  P3  Moral-Structure Clarity    within1=0.80 spearman=+0.30 wkappa=+0.38 |d|=0.70 conf=3.48
  P4  Meaning Structure          within1=0.80 spearman=+0.81 wkappa=+0.70 |d|=0.97 conf=3.82
  P5  Agency Model               within1=0.70 spearman=+0.69 wkappa=+0.60 |d|=1.00 conf=3.7
  A1  Valence                    within1=1.00 spearman=+0.83 wkappa=+0.91 |d|=0.37 conf=4.15
  A2  Emotional Volatility       within1=0.73 spearman=+0.68 wkappa=+0.51 |d|=0.87 conf=3.83
  A3  Dominant Affect            exact=0.67 kappa=+0.58 conf=4.02
  A4  Intensity Curve            within1=0.97 spearman=+0.87 wkappa=+0.80 |d|=0.60 conf=3.98
  A5  Resolution Type            exact=0.67 kappa=+0.44 conf=3.78
  S1  Rhythm Regularity          within1=0.83 spearman=+0.39 wkappa=+0.35 |d|=0.87 conf=3.8
  S2  Sentence-Length Variance   within1=0.90 spearman=+0.55 wkappa=+0.60 |d|=0.87 conf=4.3
  S3  Voice Dominance            within1=0.77 spearman=+0.81 wkappa=+0.53 |d|=1.13 conf=4.45
  S4  Figurative Density         within1=0.73 spearman=+0.84 wkappa=+0.81 |d|=0.93 conf=4.43
  S5  Aesthetic Register         exact=0.80 kappa=+0.62 conf=4.27

## Reliable axes (26): L2, L4, L5, N1, N2, N3, N4, N5, C1, C2, C3, C4, C5, P1, P2, P3, P4, P5, A1, A2, A4, S1, S2, S3, S4, S5
## Ambiguous axes (2): L1, L3

## Redundant axis pairs (|r| >= 0.8)
  C1 ~ C3  r=+0.96
  C3 ~ C5  r=+0.94
  C1 ~ C5  r=+0.93
  C5 ~ S4  r=+0.87
  L1 ~ L2  r=+0.87
  L1 ~ L3  r=+0.86
  N2 ~ N4  r=+0.86
  N5 ~ C5  r=+0.86
  N5 ~ C1  r=+0.85
  N3 ~ C2  r=+0.84
  L2 ~ L3  r=+0.83
  C3 ~ S4  r=+0.82
  L2 ~ S4  r=+0.81
  P1 ~ P2  r=+0.81
  N5 ~ C3  r=+0.81

## PCA over scalar axes
  explained variance (top): [0.4484, 0.1152, 0.105, 0.0699, 0.0555, 0.0484, 0.036, 0.0322]
  cumulative (top): [0.4484, 0.5636, 0.6686, 0.7385, 0.794, 0.8424, 0.8784, 0.9106]
  components for 80% / 90%: 6 / 8
  top-loading axes per component:
    PC1: S4(+0.25), C5(+0.25), C3(+0.24), N4(+0.24), P5(+0.24)
    PC2: P4(+0.49), P3(+0.40), A4(-0.29), P2(+0.29), N3(+0.25)
    PC3: A2(+0.36), L3(-0.34), L1(-0.34), S1(-0.30), C1(+0.29)
    PC4: N5(+0.39), S1(+0.36), L1(-0.29), L3(-0.29), S2(-0.26)
    PC5: S1(+0.46), N1(+0.41), L5(+0.34), A4(+0.31), A2(+0.28)
    PC6: C4(+0.60), N2(+0.41), N4(+0.27), P1(-0.25), N1(+0.24)

## Twin-pair consistency (mean |d| over scalar axes)
  twin pairs: 4   twin mean: 0.509   all-pairs mean: 1.494
