"""Shared gamma-exposure helpers for the options scripts.

The gamma flip (zero-gamma level) used to be implemented four times, once per
script, and one copy missed the filter for strikes without exposure. Every
script now calls ``gamma_flip_level`` so the rule lives in one place.
"""

from __future__ import annotations

import numpy as np


def gamma_flip_crossings(strikes, net_gex) -> list[float]:
    """Every strike where cumulative net GEX changes sign, in ascending order.

    Strikes with ``net_gex == 0`` (typically no open interest) are left out of
    the sign search. Without that filter the cumulative sum sits at sign 0 over
    those strikes and ``np.sign`` reports a spurious "change" where the first
    real data begins, instead of a genuine flip. The cumulative values used are
    the real ones: zero-exposure strikes add nothing to the sum.

    Crossings are detected in either direction and located by linear
    interpolation between the two strikes around each one.
    """
    k = np.asarray(strikes, dtype=float)
    g = np.asarray(net_gex, dtype=float)
    valid = np.isfinite(k) & np.isfinite(g)
    k, g = k[valid], g[valid]
    if k.size < 2:
        return []

    order = np.argsort(k, kind="stable")
    k, g = k[order], g[order]
    cum = np.cumsum(g)

    significant = g != 0
    k_sig, cum_sig = k[significant], cum[significant]
    if k_sig.size < 2:
        return []

    crossings = []
    for i in np.flatnonzero(np.diff(np.sign(cum_sig)) != 0):
        x0, x1 = k_sig[i], k_sig[i + 1]
        y0, y1 = cum_sig[i], cum_sig[i + 1]
        crossings.append(float(x0) if y1 == y0 else float(x0 - y0 * (x1 - x0) / (y1 - y0)))
    return crossings


def gamma_flip_level(strikes, net_gex, spot=None, max_distance_pct=None) -> float:
    """Gamma flip: a strike where cumulative net GEX changes sign, or NaN.

    Without ``spot`` it is the first crossing from the lowest strike (the
    original rule). With ``spot`` it is the crossing nearest to spot and, with
    ``max_distance_pct``, only one within ``spot * (1 +/- max_distance_pct)``.
    The first crossing depends on where the strike window starts: a small
    crossing at its lower edge wins over the one that matters near spot.
    """
    crossings = gamma_flip_crossings(strikes, net_gex)
    if spot is None or not np.isfinite(spot):
        return crossings[0] if crossings else np.nan
    if max_distance_pct is not None:
        crossings = [c for c in crossings if abs(c - spot) <= max_distance_pct * spot]
    if not crossings:
        return np.nan
    return min(crossings, key=lambda c: abs(c - spot))
