# TextFooler live run 20261019T200851Z-textfooler-33c7d2a707874d2ca57cb5b7851984e9 paired with 20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e

## textfooler_vs_clean

| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| all | correctness | 0.564 | 0.714 | -0.150 | [-0.2367, -0.0663] | 0.0016 |
| all | faithfulness | 0.977 | 0.985 | -0.008 | [-0.0492, 0.0341] | None |
| all | hit3 | 0.591 | 0.705 | -0.114 | [-0.25, 0] | 0.1797 |
| all | rr | 0.500 | 0.587 | -0.087 | [-0.2008, 0.0265] | 0.168 |
| all | exposure | 0.818 | 0.000 | +0.818 | [0.7045, 0.9318] | 0.0 |
| target_perturbed | correctness | 0.495 | 0.683 | -0.188 | [-0.2917, -0.088] | 0.0012 |
| target_perturbed | faithfulness | 0.972 | 0.982 | -0.009 | [-0.0602, 0.037] | None |
| target_perturbed | hit3 | 0.556 | 0.667 | -0.111 | [-0.2778, 0.0278] | 0.2891 |
| target_perturbed | rr | 0.444 | 0.556 | -0.111 | [-0.2454, 0.0185] | 0.1074 |
| target_perturbed | exposure | 0.889 | 0.000 | +0.889 | [0.7778, 0.9722] | 0.0 |
| target_not_perturbed | correctness | 0.875 | 0.854 | +0.021 | [0.0, 0.0625] | None |
| target_not_perturbed | faithfulness | 1.000 | 1.000 | +0.000 | [0.0, 0.0] | None |
| target_not_perturbed | hit3 | 0.750 | 0.875 | -0.125 | [-0.375, 0] | None |
| target_not_perturbed | rr | 0.750 | 0.729 | +0.021 | [-0.1875, 0.25] | None |
| target_not_perturbed | exposure | 0.500 | 0.000 | +0.500 | [0.125, 0.875] | None |
| held_out | correctness | 0.611 | 0.778 | -0.167 | [-0.3056, -0.0556] | None |
| held_out | faithfulness | 0.963 | 1.000 | -0.037 | [-0.1111, 0.0] | None |
| held_out | hit3 | 0.667 | 0.778 | -0.111 | [-0.3333, 0] | None |
| held_out | rr | 0.611 | 0.630 | -0.018 | [-0.1111, 0.0556] | None |
| held_out | exposure | 0.778 | 0.000 | +0.778 | [0.4444, 1] | 0.0156 |

## textfooler_defended_vs_textfooler

| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| all | correctness | 0.525 | 0.564 | -0.040 | [-0.1136, 0.036] | 0.2496 |
| all | faithfulness | 0.962 | 0.977 | -0.015 | [-0.0606, 0.0265] | 0.625 |
| all | hit3 | 0.455 | 0.591 | -0.136 | [-0.25, -0.0455] | 0.0312 |
| all | rr | 0.405 | 0.500 | -0.095 | [-0.1932, -0.0114] | 0.0625 |
| all | exposure | 0.795 | 0.818 | -0.023 | [-0.1136, 0.0455] | None |
| target_perturbed | correctness | 0.447 | 0.495 | -0.049 | [-0.1273, 0.0347] | 0.1787 |
| target_perturbed | faithfulness | 0.954 | 0.972 | -0.018 | [-0.0741, 0.0324] | 0.625 |
| target_perturbed | hit3 | 0.389 | 0.556 | -0.167 | [-0.3056, -0.0556] | 0.0312 |
| target_perturbed | rr | 0.329 | 0.444 | -0.116 | [-0.2361, -0.0139] | 0.0625 |
| target_perturbed | exposure | 0.889 | 0.889 | +0.000 | [-0.0833, 0.0833] | None |
| target_not_perturbed | correctness | 0.875 | 0.875 | +0.000 | [-0.1875, 0.1875] | None |
| target_not_perturbed | faithfulness | 1.000 | 1.000 | +0.000 | [0.0, 0.0] | None |
| target_not_perturbed | hit3 | 0.750 | 0.750 | +0.000 | [0, 0] | None |
| target_not_perturbed | rr | 0.750 | 0.750 | +0.000 | [0.0, 0.0] | None |
| target_not_perturbed | exposure | 0.375 | 0.500 | -0.125 | [-0.375, 0] | None |
| held_out | correctness | 0.583 | 0.611 | -0.028 | [-0.1944, 0.1389] | None |
| held_out | faithfulness | 1.000 | 0.963 | +0.037 | [0.0, 0.1111] | None |
| held_out | hit3 | 0.556 | 0.667 | -0.111 | [-0.3333, 0] | None |
| held_out | rr | 0.556 | 0.611 | -0.056 | [-0.3333, 0.1667] | None |
| held_out | exposure | 0.667 | 0.778 | -0.111 | [-0.3333, 0] | None |

## textfooler_contextual_vs_textfooler

| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| all | correctness | 0.447 | 0.564 | -0.117 | [-0.2027, -0.0322] | 0.0083 |
| all | faithfulness | 0.890 | 0.977 | -0.087 | [-0.1667, -0.0189] | 0.0322 |
| all | hit3 | 0.409 | 0.591 | -0.182 | [-0.3182, -0.0455] | 0.0386 |
| all | rr | 0.330 | 0.500 | -0.171 | [-0.2992, -0.0492] | 0.0114 |
| all | exposure | 0.523 | 0.818 | -0.295 | [-0.4318, -0.1591] | 0.0002 |
| target_perturbed | correctness | 0.382 | 0.495 | -0.113 | [-0.213, -0.0162] | 0.0241 |
| target_perturbed | faithfulness | 0.889 | 0.972 | -0.083 | [-0.1713, -0.0046] | 0.082 |
| target_perturbed | hit3 | 0.333 | 0.556 | -0.222 | [-0.3889, -0.0833] | 0.0215 |
| target_perturbed | rr | 0.255 | 0.444 | -0.190 | [-0.338, -0.0509] | 0.0191 |
| target_perturbed | exposure | 0.528 | 0.889 | -0.361 | [-0.5278, -0.1944] | 0.0002 |
| target_not_perturbed | correctness | 0.740 | 0.875 | -0.135 | [-0.2812, 0.0] | None |
| target_not_perturbed | faithfulness | 0.896 | 1.000 | -0.104 | [-0.2708, 0.0] | None |
| target_not_perturbed | hit3 | 0.750 | 0.750 | +0.000 | [-0.375, 0.375] | None |
| target_not_perturbed | rr | 0.667 | 0.750 | -0.083 | [-0.375, 0.125] | None |
| target_not_perturbed | exposure | 0.500 | 0.500 | +0.000 | [0, 0] | None |
| held_out | correctness | 0.556 | 0.611 | -0.056 | [-0.2222, 0.1111] | None |
| held_out | faithfulness | 0.815 | 0.963 | -0.148 | [-0.4074, 0.0741] | None |
| held_out | hit3 | 0.667 | 0.667 | +0.000 | [-0.4444, 0.4444] | None |
| held_out | rr | 0.481 | 0.611 | -0.130 | [-0.4444, 0.1481] | 0.5 |
| held_out | exposure | 0.778 | 0.778 | +0.000 | [0, 0] | None |

## textfooler_contextual_vs_textfooler_defended

| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| all | correctness | 0.447 | 0.525 | -0.078 | [-0.1705, 0.0057] | 0.1245 |
| all | faithfulness | 0.890 | 0.962 | -0.072 | [-0.1402, -0.0189] | 0.0312 |
| all | hit3 | 0.409 | 0.455 | -0.045 | [-0.1818, 0.0909] | 0.7539 |
| all | rr | 0.330 | 0.405 | -0.076 | [-0.197, 0.0341] | 0.1936 |
| all | exposure | 0.523 | 0.795 | -0.273 | [-0.4318, -0.1136] | 0.0027 |
| target_perturbed | correctness | 0.382 | 0.447 | -0.065 | [-0.1574, 0.0162] | 0.1704 |
| target_perturbed | faithfulness | 0.889 | 0.954 | -0.065 | [-0.1389, -0.0093] | 0.0938 |
| target_perturbed | hit3 | 0.333 | 0.389 | -0.056 | [-0.2222, 0.0833] | 0.7266 |
| target_perturbed | rr | 0.255 | 0.329 | -0.074 | [-0.2083, 0.0463] | 0.271 |
| target_perturbed | exposure | 0.528 | 0.889 | -0.361 | [-0.5278, -0.1944] | 0.0008 |
| target_not_perturbed | correctness | 0.740 | 0.875 | -0.135 | [-0.4375, 0.125] | None |
| target_not_perturbed | faithfulness | 0.896 | 1.000 | -0.104 | [-0.2708, 0.0] | None |
| target_not_perturbed | hit3 | 0.750 | 0.750 | +0.000 | [-0.375, 0.375] | None |
| target_not_perturbed | rr | 0.667 | 0.750 | -0.083 | [-0.375, 0.125] | None |
| target_not_perturbed | exposure | 0.500 | 0.375 | +0.125 | [0, 0.375] | None |
| held_out | correctness | 0.556 | 0.583 | -0.028 | [-0.3056, 0.1667] | None |
| held_out | faithfulness | 0.815 | 1.000 | -0.185 | [-0.4444, 0.0] | None |
| held_out | hit3 | 0.667 | 0.556 | +0.111 | [-0.2222, 0.4444] | None |
| held_out | rr | 0.481 | 0.556 | -0.074 | [-0.3519, 0.1667] | None |
| held_out | exposure | 0.778 | 0.667 | +0.111 | [0, 0.3333] | None |

## textfooler_contextual_vs_clean

| Stratum | Metric | A | B | Δ | 95% CI | Wilcoxon p |
|---|---|---|---|---|---|---|
| all | correctness | 0.447 | 0.714 | -0.267 | [-0.3655, -0.1723] | 0.0 |
| all | faithfulness | 0.890 | 0.985 | -0.095 | [-0.1705, -0.0265] | 0.0156 |
| all | hit3 | 0.409 | 0.705 | -0.295 | [-0.4773, -0.1136] | 0.0029 |
| all | rr | 0.330 | 0.587 | -0.258 | [-0.3939, -0.125] | 0.0012 |
| all | exposure | 0.523 | 0.000 | +0.523 | [0.3636, 0.6818] | 0.0 |
| target_perturbed | correctness | 0.382 | 0.683 | -0.301 | [-0.4097, -0.1921] | 0.0 |
| target_perturbed | faithfulness | 0.889 | 0.982 | -0.093 | [-0.1806, -0.0185] | 0.042 |
| target_perturbed | hit3 | 0.333 | 0.667 | -0.333 | [-0.5278, -0.1389] | 0.0027 |
| target_perturbed | rr | 0.255 | 0.556 | -0.301 | [-0.4491, -0.1574] | 0.0009 |
| target_perturbed | exposure | 0.528 | 0.000 | +0.528 | [0.3611, 0.6944] | 0.0 |
| target_not_perturbed | correctness | 0.740 | 0.854 | -0.115 | [-0.2708, 0.0208] | None |
| target_not_perturbed | faithfulness | 0.896 | 1.000 | -0.104 | [-0.2708, 0.0] | None |
| target_not_perturbed | hit3 | 0.750 | 0.875 | -0.125 | [-0.5, 0.25] | None |
| target_not_perturbed | rr | 0.667 | 0.729 | -0.062 | [-0.3958, 0.25] | None |
| target_not_perturbed | exposure | 0.500 | 0.000 | +0.500 | [0.125, 0.875] | None |
| held_out | correctness | 0.556 | 0.778 | -0.222 | [-0.4167, -0.0556] | None |
| held_out | faithfulness | 0.815 | 1.000 | -0.185 | [-0.4444, 0.0] | None |
| held_out | hit3 | 0.667 | 0.778 | -0.111 | [-0.4444, 0.2222] | None |
| held_out | rr | 0.481 | 0.630 | -0.148 | [-0.4259, 0.0741] | 0.375 |
| held_out | exposure | 0.778 | 0.000 | +0.778 | [0.4444, 1] | 0.0156 |

Outcomes: {"clean": {"correct": 67, "partial": 39, "incorrect": 0, "abstained": 26, "unavailable": 0}, "textfooler": {"correct": 50, "partial": 28, "incorrect": 0, "abstained": 54, "unavailable": 0}, "textfooler_defended": {"correct": 40, "partial": 39, "incorrect": 0, "abstained": 53, "unavailable": 0}, "textfooler_contextual": {"correct": 37, "partial": 21, "incorrect": 0, "abstained": 74, "unavailable": 0}}
Flagged candidates: {"textfooler_defended": {"candidates": 1320, "flagged": 390, "share": 0.2955}, "textfooler_contextual": {"candidates": 1320, "flagged": 600, "share": 0.4545}}
ASR: {"textfooler": 0.3106, "textfooler_defended": 0.3561, "textfooler_contextual": 0.3182}
