"""Reference functions for Stepik tasks using only the standard library.

Each function is a separate task. Transfer statement and tests to the editor;
this file is not a Stepik API import payload.
"""

import math


def p_activity(value: float, unit: str) -> float:
    scales = {"M": 1.0, "mM": 1e-3, "uM": 1e-6, "nM": 1e-9}
    if unit not in scales or not math.isfinite(value) or value <= 0:
        raise ValueError("invalid concentration")
    return -math.log10(value * scales[unit])


def tanimoto(a: set[int], b: set[int]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def enrichment(total: int, active: int, k: int, top_active: int) -> float:
    if not (0 < active <= total and 0 < k <= total and
            0 <= top_active <= min(k, active) and active - top_active <= total - k):
        raise ValueError("inconsistent counts")
    return (top_active / k) / (active / total)


def z_prime(mu_pos: float, mu_neg: float, sd_pos: float, sd_neg: float) -> float:
    values = (mu_pos, mu_neg, sd_pos, sd_neg)
    if not all(math.isfinite(x) for x in values) or min(sd_pos, sd_neg) < 0 or mu_pos == mu_neg:
        raise ValueError("invalid controls")
    return 1.0 - 3.0 * (sd_pos + sd_neg) / abs(mu_pos - mu_neg)
