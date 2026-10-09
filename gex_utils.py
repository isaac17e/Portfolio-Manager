"""Shared gamma-exposure helpers for the options scripts.

Two different levels live here:

- ``zero_gamma_profile``: the zero-gamma level S*, the hypothetical spot where
  total dealer GEX, re-evaluated at that spot, is zero. This is the level the
  rule "spot above it -> positive gamma" refers to, and the one every script
  now reports as its flip / zero-gamma level.
- ``gamma_flip_level`` / ``gamma_flip_crossings``: the strike where the
  CUMULATIVE per-strike GEX (all gammas at the current spot) changes sign. That
  is a strike-balance level, not S*: with mostly out-of-the-money open interest
  it can sit on the other side of spot from S* (day 2: AVGO positive GEX, spot
  362.6, cumulative crossing 399.7). Kept as ``strike_balance_level``.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import brentq

# Spot grid for the GEX profile: spot * (1 +/- ZERO_GAMMA_GRID_HALF_WIDTH) in
# ZERO_GAMMA_GRID_POINTS evenly spaced points. An odd count puts the current
# spot on the centre node. 181 points over +/-30% is a 0.33% step; each
# crossing is then refined with brentq on the exact Black-Scholes sum, so the
# step only has to be fine enough not to jump over two crossings.
ZERO_GAMMA_GRID_HALF_WIDTH = 0.30
ZERO_GAMMA_GRID_POINTS = 181
# Points kept when the profile is exported in a signal (downsampled, spot on a node).
ZERO_GAMMA_EXPORT_POINTS = 31
# Dollar GEX per 1% move: gamma * OI * 100 * S^2 * 0.01, as every script does at spot.
GEX_PER_PCT_MOVE = 0.01
CONTRACT_MULTIPLIER = 100

STATUS_OK = "ok"
STATUS_NO_CROSSING = "no_crossing_in_grid"
STATUS_NO_CONTRACTS = "no_valid_contracts"
STATUS_NO_SPOT = "no_spot"


def bs_gamma_matrix(spots, strikes, T, iv, r, q=0.0):
    """Black-Scholes gamma, contracts x spots. ``strikes``, ``T``, ``iv`` and ``q``
    are per contract (``q`` may be a scalar); inputs must already be valid."""
    S = np.asarray(spots, dtype=float)[None, :]
    K = np.asarray(strikes, dtype=float)[:, None]
    T = np.asarray(T, dtype=float)[:, None]
    sigma = np.asarray(iv, dtype=float)[:, None]
    q = np.broadcast_to(np.asarray(q, dtype=float), np.shape(strikes))[:, None]
    vol = sigma * np.sqrt(T)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / vol
    return np.exp(-q * T) * np.exp(-0.5 * d1 ** 2) / (np.sqrt(2.0 * np.pi) * S * vol)


def _valid_contracts(strikes, is_call, open_interest, iv, T, q):
    """Per-contract arrays restricted to contracts that can be priced.

    Contracts without open interest add nothing and are not counted. Contracts
    with open interest but missing / non-positive IV or T <= 0 are skipped and
    counted: they are in the at-spot GEX (their gamma came from the chain) but
    cannot be re-evaluated at other spots.
    """
    k = np.asarray(strikes, dtype=float)
    oi = np.asarray(open_interest, dtype=float)
    sigma = np.asarray(iv, dtype=float)
    t = np.asarray(T, dtype=float)
    q = np.broadcast_to(np.asarray(q, dtype=float), k.shape)
    sign = np.where(np.asarray(is_call, dtype=bool), 1.0, -1.0)
    with np.errstate(invalid="ignore"):
        exposed = np.isfinite(k) & (k > 0) & np.isfinite(oi) & (oi > 0)
        valid = exposed & np.isfinite(sigma) & (sigma > 0) & np.isfinite(t) & (t > 0) & np.isfinite(q)
    weights = sign[valid] * oi[valid] * CONTRACT_MULTIPLIER
    return (k[valid], t[valid], sigma[valid], q[valid], weights), int((exposed & ~valid).sum())


def _net_gex(spots, contracts, r, scale):
    k, t, sigma, q, weights = contracts
    S = np.asarray(spots, dtype=float)
    if k.size == 0:
        return np.zeros_like(S)
    return (weights @ bs_gamma_matrix(S, k, t, sigma, r, q)) * S ** 2 * scale


def zero_gamma_profile(strikes, is_call, open_interest, iv, T, spot, r, q=0.0,
                       half_width=ZERO_GAMMA_GRID_HALF_WIDTH, n_points=ZERO_GAMMA_GRID_POINTS,
                       scale=GEX_PER_PCT_MOVE):
    """Dealer GEX re-evaluated on a spot grid, and the zero-gamma level.

    GEX_total(S) = sum over contracts of +/- gamma_BS(S; K, T, IV, r, q) * OI
    * 100 * S^2 * ``scale``: calls +, puts - (the dealer convention every
    script uses), same multiplier and per-1% scaling as the at-spot GEX, so
    ``gex_at_spot`` matches the script's net GEX when its gammas are
    Black-Scholes gammas at the same IV / T / r / q.

    Sticky strike: each contract keeps its own IV as spot moves. A
    sticky-moneyness variant needs the smile per expiry interpolated at
    K * spot / S and is not implemented.

    Every sign change on the grid is refined with brentq on the exact sum;
    ``zero_gamma_level`` is the crossing nearest spot. With no crossing in the
    grid it is None and ``zero_gamma_status`` is "no_crossing_in_grid", with
    ``grid_sign`` "all_positive" / "all_negative" (or "all_zero").
    """
    contracts, n_skipped = _valid_contracts(strikes, is_call, open_interest, iv, T, q)
    result = {
        "zero_gamma_level": None, "zero_gamma_crossings": [], "zero_gamma_status": STATUS_OK,
        "zero_gamma_below": None, "zero_gamma_above": None, "grid_sign": None,
        "gex_at_spot": None, "grid": np.array([]), "gex": np.array([]),
        "n_contracts": int(contracts[0].size), "n_skipped": n_skipped,
        "model": "sticky_strike", "grid_half_width": half_width,
    }
    if spot is None or not np.isfinite(spot) or spot <= 0:
        result["zero_gamma_status"] = STATUS_NO_SPOT
        return result
    if contracts[0].size == 0:
        result["zero_gamma_status"] = STATUS_NO_CONTRACTS
        return result

    grid = np.linspace(spot * (1.0 - half_width), spot * (1.0 + half_width), int(n_points))
    gex = _net_gex(grid, contracts, r, scale)
    result.update(grid=grid, gex=gex, gex_at_spot=float(_net_gex([spot], contracts, r, scale)[0]))

    def f(s):
        return float(_net_gex([s], contracts, r, scale)[0])

    # Sign changes between consecutive non-zero grid values (a zero node lies
    # inside the bracket and brentq finds it).
    nonzero = np.flatnonzero(gex != 0)
    crossings = []
    for a, b in zip(nonzero[:-1], nonzero[1:]):
        if np.sign(gex[a]) != np.sign(gex[b]):
            crossings.append(float(brentq(f, grid[a], grid[b], xtol=1e-9 * spot)))
    result["zero_gamma_crossings"] = crossings

    if not crossings:
        result["zero_gamma_status"] = STATUS_NO_CROSSING
        result["grid_sign"] = ("all_zero" if nonzero.size == 0
                               else "all_positive" if gex[nonzero[0]] > 0 else "all_negative")
        return result
    below = [c for c in crossings if c <= spot]
    above = [c for c in crossings if c > spot]
    result.update(
        zero_gamma_level=min(crossings, key=lambda c: abs(c - spot)),
        zero_gamma_below=max(below) if below else None,
        zero_gamma_above=min(above) if above else None,
    )
    return result


def downsample_profile(profile, n_points=ZERO_GAMMA_EXPORT_POINTS):
    """Compact ``[[spot, gex], ...]`` copy of a profile for a JSON signal."""
    grid, gex = profile.get("grid"), profile.get("gex")
    if grid is None or len(grid) == 0:
        return []
    idx = np.unique(np.round(np.linspace(0, len(grid) - 1, int(n_points))).astype(int))
    return [[round(float(grid[i]), 4), round(float(gex[i]), 2)] for i in idx]


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
    """Strike-balance level: a strike where cumulative net GEX changes sign, or NaN.

    Not the zero-gamma level (see ``zero_gamma_profile``).

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
