# Defence evaluation: 20261017T165331Z-defence-cebfb27c1e9048cdb61fbfe15f37e50d paired with 20261016T222418Z-8160ce1aa8a04e559bc15ee060f7587e
132 pairs, 44 questions.

## defended_vs_poisoned

| Stratum | Metric | A | B | Δ (A−B) | 95% CI | Wilcoxon p | improved / worsened |
|---|---|---|---|---|---|---|---|
| all | correctness | 0.526 | 0.555 | -0.028 | [-0.0833, 0.0265] | 0.293 | 4 / 8 |
| all | faithfulness | 0.967 | 0.943 | +0.024 | [-0.0174, 0.0659] | 0.4375 | 4 / 1 |
| all | hit3 | 0.477 | 0.568 | -0.091 | [-0.2045, 0] | 0.2188 | 1 / 5 |
| all | rr | 0.409 | 0.485 | -0.076 | [-0.1856, 0.0189] | 0.1641 | 5 / 7 |
| all | exposure | 0.273 | 0.409 | -0.136 | [-0.25, -0.0455] | 0.0312 | 0 / 6 |
| target_perturbed | correctness | 0.361 | 0.432 | -0.071 | [-0.1327, -0.0185] | 0.0234 | 1 / 7 |
| target_perturbed | faithfulness | 0.946 | 0.926 | +0.020 | [-0.037, 0.0778] | None | 3 / 1 |
| target_perturbed | hit3 | 0.259 | 0.444 | -0.185 | [-0.3333, -0.037] | 0.0625 | 0 / 5 |
| target_perturbed | rr | 0.235 | 0.370 | -0.136 | [-0.2963, 0.0062] | 0.0859 | 2 / 6 |
| target_perturbed | exposure | 0.370 | 0.593 | -0.222 | [-0.4074, -0.0741] | 0.0312 | 0 / 6 |
| target_not_perturbed | correctness | 0.789 | 0.750 | +0.039 | [-0.0588, 0.1373] | None | 3 / 1 |
| target_not_perturbed | faithfulness | 1.000 | 0.971 | +0.029 | [0.0, 0.0882] | None | 1 / 0 |
| target_not_perturbed | hit3 | 0.824 | 0.765 | +0.059 | [0, 0.1765] | None | 1 / 0 |
| target_not_perturbed | rr | 0.686 | 0.667 | +0.020 | [-0.0882, 0.1176] | None | 3 / 1 |
| target_not_perturbed | exposure | 0.118 | 0.118 | +0.000 | [0, 0] | None | 0 / 0 |
| held_out | correctness | 0.611 | 0.630 | -0.018 | [-0.1667, 0.1389] | None | 1 / 2 |
| held_out | faithfulness | 1.000 | 1.000 | +0.000 | [0.0, 0.0] | None | 0 / 0 |
| held_out | hit3 | 0.556 | 0.667 | -0.111 | [-0.3333, 0] | None | 0 / 1 |
| held_out | rr | 0.556 | 0.667 | -0.111 | [-0.3333, 0.0] | None | 0 / 1 |
| held_out | exposure | 0.333 | 0.667 | -0.333 | [-0.6667, 0] | None | 0 / 3 |

## defended_vs_clean

| Stratum | Metric | A | B | Δ (A−B) | 95% CI | Wilcoxon p | improved / worsened |
|---|---|---|---|---|---|---|---|
| all | correctness | 0.526 | 0.714 | -0.188 | [-0.286, -0.0928] | 0.0009 | 3 / 23 |
| all | faithfulness | 0.967 | 0.985 | -0.018 | [-0.0568, 0.0189] | 0.5 | 1 / 4 |
| all | hit3 | 0.477 | 0.705 | -0.227 | [-0.3864, -0.0682] | 0.0075 | 2 / 12 |
| all | rr | 0.409 | 0.587 | -0.178 | [-0.3258, -0.0379] | 0.014 | 7 / 13 |
| all | exposure | 0.273 | 0.000 | +0.273 | [0.1591, 0.4091] | 0.0005 | 12 / 0 |
| target_perturbed | correctness | 0.361 | 0.682 | -0.321 | [-0.4352, -0.213] | 0.0001 | 0 / 19 |
| target_perturbed | faithfulness | 0.946 | 0.994 | -0.048 | [-0.0988, -0.0062] | None | 0 / 4 |
| target_perturbed | hit3 | 0.259 | 0.630 | -0.370 | [-0.5926, -0.1852] | 0.0063 | 1 / 11 |
| target_perturbed | rr | 0.235 | 0.506 | -0.272 | [-0.4753, -0.0741] | 0.0138 | 4 / 11 |
| target_perturbed | exposure | 0.370 | 0.000 | +0.370 | [0.1852, 0.5556] | 0.002 | 10 / 0 |
| target_not_perturbed | correctness | 0.789 | 0.765 | +0.025 | [-0.0882, 0.1422] | 0.8125 | 3 / 4 |
| target_not_perturbed | faithfulness | 1.000 | 0.971 | +0.029 | [0.0, 0.0882] | None | 1 / 0 |
| target_not_perturbed | hit3 | 0.824 | 0.824 | +0.000 | [-0.1765, 0.1765] | None | 1 / 1 |
| target_not_perturbed | rr | 0.686 | 0.716 | -0.029 | [-0.1961, 0.1177] | 0.875 | 3 / 2 |
| target_not_perturbed | exposure | 0.118 | 0.000 | +0.118 | [0, 0.2941] | None | 2 / 0 |
| held_out | correctness | 0.611 | 0.778 | -0.167 | [-0.3889, 0.0556] | 0.3125 | 1 / 4 |
| held_out | faithfulness | 1.000 | 1.000 | +0.000 | [0.0, 0.0] | None | 0 / 0 |
| held_out | hit3 | 0.556 | 0.778 | -0.222 | [-0.5556, 0] | None | 0 / 2 |
| held_out | rr | 0.556 | 0.630 | -0.074 | [-0.3704, 0.1852] | None | 1 / 2 |
| held_out | exposure | 0.333 | 0.000 | +0.333 | [0, 0.6667] | None | 3 / 0 |

## clean_filtered_vs_clean

| Stratum | Metric | A | B | Δ (A−B) | 95% CI | Wilcoxon p | improved / worsened |
|---|---|---|---|---|---|---|---|
| all | correctness | 0.650 | 0.714 | -0.064 | [-0.1383, 0.0019] | 0.0659 | 5 / 10 |
| all | faithfulness | 0.955 | 0.985 | -0.030 | [-0.0795, 0.0114] | 0.375 | 1 / 4 |
| all | hit3 | 0.705 | 0.705 | +0.000 | [-0.0682, 0.0682] | None | 1 / 1 |
| all | rr | 0.587 | 0.587 | -0.000 | [-0.0455, 0.0455] | 1.0 | 4 / 3 |
| all | exposure | 0.000 | 0.000 | +0.000 | [0, 0] | None | 0 / 0 |
| target_perturbed | correctness | 0.571 | 0.682 | -0.111 | [-0.2099, -0.0247] | 0.0234 | 3 / 7 |
| target_perturbed | faithfulness | 0.926 | 0.994 | -0.068 | [-0.1358, -0.0123] | None | 0 / 4 |
| target_perturbed | hit3 | 0.593 | 0.630 | -0.037 | [-0.1111, 0] | None | 0 / 1 |
| target_perturbed | rr | 0.512 | 0.506 | +0.006 | [-0.037, 0.0556] | None | 2 / 2 |
| target_perturbed | exposure | 0.000 | 0.000 | +0.000 | [0, 0] | None | 0 / 0 |
| target_not_perturbed | correctness | 0.774 | 0.765 | +0.010 | [-0.0833, 0.1078] | 1.0 | 2 / 3 |
| target_not_perturbed | faithfulness | 1.000 | 0.971 | +0.029 | [0.0, 0.0882] | None | 1 / 0 |
| target_not_perturbed | hit3 | 0.882 | 0.824 | +0.059 | [0, 0.1765] | None | 1 / 0 |
| target_not_perturbed | rr | 0.706 | 0.716 | -0.010 | [-0.1078, 0.0686] | None | 2 / 1 |
| target_not_perturbed | exposure | 0.000 | 0.000 | +0.000 | [0, 0] | None | 0 / 0 |
| held_out | correctness | 0.722 | 0.778 | -0.056 | [-0.2778, 0.1667] | None | 2 / 2 |
| held_out | faithfulness | 1.000 | 1.000 | +0.000 | [0.0, 0.0] | None | 0 / 0 |
| held_out | hit3 | 0.667 | 0.778 | -0.111 | [-0.3333, 0] | None | 0 / 1 |
| held_out | rr | 0.611 | 0.630 | -0.018 | [-0.1111, 0.0556] | None | 1 / 1 |
| held_out | exposure | 0.000 | 0.000 | +0.000 | [0, 0] | None | 0 / 0 |

Outcomes: {"clean": {"correct": 67, "partial": 39, "incorrect": 0, "abstained": 26, "unavailable": 0}, "poisoned": {"correct": 49, "partial": 36, "incorrect": 2, "abstained": 45, "unavailable": 0}, "defended": {"correct": 51, "partial": 28, "incorrect": 0, "abstained": 53, "unavailable": 0}, "clean_filtered": {"correct": 63, "partial": 33, "incorrect": 0, "abstained": 35, "unavailable": 1}}
ASR (edited exposure, drop ≥0.25): {"poisoned": 0.1667, "defended": 0.1061}
Unavailable observations (kept as missing, never zero): {"clean": {"correctness": 0, "faithfulness": 0, "hit3": 0, "rr": 0, "exposure": 0}, "poisoned": {"correctness": 0, "faithfulness": 0, "hit3": 0, "rr": 0, "exposure": 0}, "defended": {"correctness": 0, "faithfulness": 1, "hit3": 0, "rr": 0, "exposure": 0}, "clean_filtered": {"correctness": 1, "faithfulness": 1, "hit3": 1, "rr": 1, "exposure": 1}}
