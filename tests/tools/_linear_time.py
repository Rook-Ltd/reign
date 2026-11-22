"""Linear-time assertions that hold on slower CI runners.

Upstream bounds each scan at 2 seconds on its 32-vCPU runners. On a 4-vCPU GitHub runner the
same linear scan can take 3 seconds. A quadratic scan, the bug these tests guard against, takes
about 16 times as long on 4 times the input, so when the wall-clock bound is missed the input
is timed again at a quarter of its size and the growth ratio decides.
"""
from __future__ import annotations

import time
from collections.abc import Callable

BUDGET_SECONDS = 2.0
MAX_GROWTH_AT_4X = 8.0  # linear is about 4; quadratic is about 16


def _timed(scan: Callable[[str], object], command: str) -> float:
    start = time.perf_counter()
    scan(command)
    return time.perf_counter() - start


def assert_scans_in_linear_time(scan: Callable[[str], object], build: Callable[[int], str], n: int) -> None:
    full = _timed(scan, build(n))
    if full < BUDGET_SECONDS:
        return
    quarter = _timed(scan, build(n // 4))
    assert full < MAX_GROWTH_AT_4X * quarter, (
        f"{build(2)[:30]!r}: {full:.2f}s at n={n} vs {quarter:.2f}s at n={n // 4}, which is not linear"
    )
