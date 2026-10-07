"""Shared gamma-exposure helpers for the options scripts.

The gamma flip (zero-gamma level) used to be implemented four times, once per
script, and one copy missed the filter for strikes without exposure. Every
script now calls ``gamma_flip_level`` so the rule lives in one place.
"""

from __future__ import annotations

import numpy as np


def gamma_flip_level(strikes, net_gex) -> float:
    """Strike where cumulative net GEX first changes sign, or NaN if it never does.

    Strikes with ``net_gex == 0`` (typically no open interest) are left out of
    the sign search. Without that filter the cumulative sum sits at sign 0 over
    those strikes and ``np.sign`` reports a spurious "change" where the first
    real data begins, instead of a genuine flip. The cumulative values used are
    the real ones: zero-exposure strikes add nothing to the sum.

    The crossing is detected in either direction and located by linear
    interpolation between the two strikes around it.
    """
    k = np.asarray(strikes, dtype=float)
    g = np.asarray(net_gex, dtype=float)
    valid = np.isfinite(k) & np.isfinite(g)
    k, g = k[valid], g[valid]
    if k.size < 2:
        return np.nan

    order = np.argsort(k, kind="stable")
    k, g = k[order], g[order]
    cum = np.cumsum(g)

    significant = g != 0
    k_sig, cum_sig = k[significant], cum[significant]
    if k_sig.size < 2:
        return np.nan

    change = np.flatnonzero(np.diff(np.sign(cum_sig)) != 0)
    if change.size == 0:
        return np.nan
    i = change[0]
    x0, x1 = k_sig[i], k_sig[i + 1]
    y0, y1 = cum_sig[i], cum_sig[i + 1]
    if y1 == y0:
        return float(x0)
    return float(x0 - y0 * (x1 - x0) / (y1 - y0))
