"""Map a canonical portfolio ticker to provider symbols.

The canonical form is the symbol stored in the portfolio file. Class shares
may use a hyphen (``BRK-B``) or a dot (``BRK.B``).

- Yahoo Finance uses the hyphen and keeps exchange suffixes: ``BRK-B``, ``RY.TO``.
- Polygon uses the dot: ``BRK.B``. Listings with an exchange suffix such as
  ``.TO`` have no US-listed options, so options scripts must skip them.
- Capital.com epics listed in ``_CAPITAL_VERIFIED`` were checked against the
  Capital.com API (``BRK-B`` -> ``BRKB``, ``RY.TO`` -> ``RY``). Any other epic
  is a best-effort guess (class shares keep the Polygon dot; an exchange
  suffix is stripped), is **not** verified and must be checked before any order.

``to_yahoo`` / ``to_polygon`` / ``to_capital_epic`` are idempotent for the
forms above.

International tickers keep their local symbol as the portfolio key (the
optimizer's ``RY.TO``). ``resolve_instrument`` decides how to analyse and trade
them, in tiers:

- ``native``: no exchange suffix; the ticker itself has US options.
- ``adr``: a US ADR / twin listing in ``_ADR_TABLE`` (``RY.TO`` -> ``RY``).
  Options and Capital.com orders go through the US symbol. Unverified entries
  may be used for analysis (with a warning) but get no Capital.com epic.
- ``proxy``: no ADR; the country ETF of the exchange suffix
  (``_PROXY_ETF_BY_SUFFIX``) stands in for IV / gamma / put-call.
- ``none``: no ADR and no proxy ETF.
"""

from __future__ import annotations

import os
import re

# Longer suffixes first so ".TWO" wins over ".TW".
_EXCHANGE_SUFFIXES = (
    ".TWO",
    ".CN", ".NE", ".TO", ".HK", ".AX", ".NZ", ".KS", ".KQ",
    ".TW", ".SS", ".SZ", ".NS", ".BO", ".SA", ".MX", ".JO", ".SR",
    ".PA", ".DE", ".BE", ".MU", ".HM", ".DU", ".SG", ".AS", ".BR",
    ".LS", ".MC", ".MI", ".SW", ".VI", ".WA", ".ST", ".OL", ".CO",
    ".HE", ".IR", ".PR", ".IL", ".TA",
    ".V", ".L", ".F", ".T",
)

# US ADR / twin listings of international tickers, keyed by the Yahoo form of
# the local ticker. ``verified`` means the Capital.com epic was checked against
# the Capital.com API on ``verified_on``; only verified entries may be traded.
# Add new entries with ``verified: False`` until the epic is confirmed.
_ADR_TABLE = {
    "RY.TO": {
        "us_ticker": "RY",
        "polygon_ticker": "RY",
        "capital_epic": "RY",
        "currency": "USD",
        "listing": "NYSE",
        "ratio": 1.0,  # interlisted common share, not a depositary receipt
        "verified": True,
        "verified_on": "2026-10-06",
    },
}

# Country ETF whose US options stand in for a listing without options or ADR.
# Mapped from the Yahoo exchange suffix. Suffixes left out (``.LS``, ``.PR``)
# have no liquid US-listed country ETF and fall to tier ``none``.
_PROXY_ETF_BY_SUFFIX = {
    ".TO": "EWC", ".V": "EWC", ".CN": "EWC", ".NE": "EWC",
    ".T": "EWJ",
    ".SA": "EWZ",
    ".DE": "EWG", ".F": "EWG", ".BE": "EWG", ".MU": "EWG", ".HM": "EWG",
    ".DU": "EWG", ".SG": "EWG",
    ".L": "EWU", ".IL": "EWU",
    ".PA": "EWQ",
    ".SW": "EWL",
    ".AX": "EWA",
    ".HK": "EWH",
    ".SS": "MCHI", ".SZ": "MCHI",
    ".NS": "INDA", ".BO": "INDA",
    ".MX": "EWW",
    ".KS": "EWY", ".KQ": "EWY",
    ".TW": "EWT", ".TWO": "EWT",
    ".AS": "EWN", ".MC": "EWP", ".MI": "EWI", ".ST": "EWD", ".BR": "EWK",
    ".CO": "EDEN", ".HE": "EFNL", ".OL": "NORW", ".IR": "EIRL", ".WA": "EPOL",
    ".VI": "EWO", ".JO": "EZA", ".SR": "KSA", ".NZ": "ENZL", ".TA": "EIS",
}

# Tier ``none``: the target weight is capped at ``factor`` x target and, if set,
# at an absolute weight. Override with these environment variables.
NO_OPTIONS_CAP_FACTOR_ENV = "NO_OPTIONS_WEIGHT_CAP_FACTOR"
NO_OPTIONS_CAP_ENV = "NO_OPTIONS_WEIGHT_CAP"
DEFAULT_NO_OPTIONS_CAP_FACTOR = 0.5

# Capital.com epics verified against the Capital.com API on 2026-10-06, keyed by
# the Yahoo form of the ticker. ``RY`` is the NYSE listing quoted in USD:
# Capital.com has no TSX/CAD line for Royal Bank of Canada. Verified ADR epics
# come from ``_ADR_TABLE``.
_CAPITAL_VERIFIED_ON = "2026-10-06"
_CAPITAL_VERIFIED = {
    "BRK-B": {"epic": "BRKB"},  # "BRK.B" does not exist; "BRKb" -> error.not-found.epic
    **{
        local: {"epic": adr["capital_epic"], "currency": adr["currency"], "listing": adr["listing"]}
        for local, adr in _ADR_TABLE.items()
        if adr.get("verified") and adr.get("capital_epic")
    },
}

_CLASS = re.compile(r"^([A-Z0-9]{1,6})[.-]([A-Z])$")


def _clean(ticker) -> str:
    return str(ticker).strip()


def _upper(ticker) -> str:
    return _clean(ticker).upper()


def exchange_suffix(ticker) -> str | None:
    """Yahoo-style exchange suffix (``.TO``, ``.L``, ...), if present."""
    symbol = _upper(ticker)
    for suffix in _EXCHANGE_SUFFIXES:
        if symbol.endswith(suffix) and len(symbol) > len(suffix):
            return suffix
    return None


def _split_listing(ticker) -> tuple[str, str]:
    symbol = _upper(ticker)
    suffix = exchange_suffix(symbol) or ""
    base = symbol[: -len(suffix)] if suffix else symbol
    return base, suffix


def _class_parts(base: str) -> tuple[str, str] | None:
    match = _CLASS.match(base)
    if not match:
        return None
    return match.group(1), match.group(2)


def _format_class(base: str, separator: str) -> str:
    parts = _class_parts(base)
    if not parts:
        return base
    return f"{parts[0]}{separator}{parts[1]}"


def to_yahoo(ticker) -> str:
    """Yahoo symbol: ``BRK-B``, ``RY.TO``."""
    base, suffix = _split_listing(ticker)
    return _format_class(base, "-") + suffix


def to_polygon(ticker) -> str:
    """Polygon symbol: ``BRK.B``. Exchange suffixes are preserved (no US options)."""
    base, suffix = _split_listing(ticker)
    return _format_class(base, ".") + suffix


def to_capital_epic(ticker) -> str:
    """Capital.com epic: verified (see ``_CAPITAL_VERIFIED``) or a best guess.

    ``BRK-B`` -> ``BRKB``; ``RY.TO`` -> ``RY`` (NYSE listing in USD, not TSX).
    Otherwise class shares keep the Polygon dot and an exchange suffix is
    stripped, which is only a guess — confirm with the broker.
    """
    verified = _CAPITAL_VERIFIED.get(to_yahoo(ticker))
    if verified:
        return verified["epic"]
    base, _suffix = _split_listing(ticker)
    return _format_class(base, ".")


def capital_epic_verified(ticker) -> bool:
    """True if the epic was checked against Capital.com (``_CAPITAL_VERIFIED``)."""
    return to_yahoo(ticker) in _CAPITAL_VERIFIED


def no_us_options_reason(ticker) -> str | None:
    """Why this listing has no US-listed options, or None if it might."""
    if not _clean(ticker):
        return "empty ticker"
    suffix = exchange_suffix(ticker)
    if suffix:
        return f"no US-listed options (exchange suffix {suffix})"
    return None


def has_us_options(ticker) -> bool:
    return no_us_options_reason(ticker) is None


def partition_us_options(tickers):
    """Split tickers into ``(eligible, excluded)``.

    ``excluded`` is a list of ``{"ticker", "reason"}`` using the original key.
    """
    eligible = []
    excluded = []
    for ticker in tickers:
        reason = no_us_options_reason(ticker)
        if reason:
            excluded.append({"ticker": _clean(ticker), "reason": reason})
        else:
            eligible.append(ticker)
    return eligible, excluded


def exclusion_warnings(excluded) -> list[str]:
    warnings = []
    for item in excluded or []:
        warnings.append(f"{item.get('ticker')}: {item.get('reason')}")
    return warnings


def mapping(ticker) -> dict:
    """All provider forms plus whether US options can exist."""
    return {
        "canonical": _clean(ticker),
        "yahoo": to_yahoo(ticker),
        "polygon": to_polygon(ticker),
        "capital_epic": to_capital_epic(ticker),
        "capital_epic_verified": capital_epic_verified(ticker),
        "has_us_options": has_us_options(ticker),
        "us_options_reason": no_us_options_reason(ticker),
    }


def proxy_etf(ticker) -> str | None:
    """Country ETF for the exchange suffix of ``ticker``, if one is mapped."""
    suffix = exchange_suffix(ticker)
    return _PROXY_ETF_BY_SUFFIX.get(suffix) if suffix else None


def resolve_instrument(ticker) -> dict:
    """How to analyse and trade ``ticker`` (see the module docstring for tiers).

    ``local`` stays the portfolio key. ``analysis_ticker`` is the symbol whose
    US options are read (the ticker itself or its ADR); for ``proxy`` and
    ``none`` it is the local listing, used only for Yahoo prices.
    ``capital_epic`` is set only when it may be used for an order: verified for
    ADRs, the usual ``to_capital_epic`` form for native tickers (check
    ``capital_epic_verified``), and None otherwise. ``verified`` is True when no
    mapping is needed (native) or the ADR entry is verified.
    """
    local = _clean(ticker)
    info = {
        "local": local,
        "yahoo_ticker": to_yahoo(ticker) if local else "",
        "analysis_ticker": local,
        "polygon_ticker": None,
        "capital_epic": None,
        "capital_epic_verified": False,
        "tier": "none",
        "proxy_etf": None,
        "verified": False,
        "verified_on": None,
        "currency": None,
        "listing": None,
        "ratio": None,
        "reason": no_us_options_reason(ticker),
        "warnings": [],
    }
    if not local:
        return info

    adr = _ADR_TABLE.get(info["yahoo_ticker"])
    if adr:
        verified = bool(adr.get("verified"))
        info.update({
            "tier": "adr",
            "analysis_ticker": adr["us_ticker"],
            "polygon_ticker": adr.get("polygon_ticker") or to_polygon(adr["us_ticker"]),
            "capital_epic": adr.get("capital_epic") if verified else None,
            "capital_epic_verified": verified and bool(adr.get("capital_epic")),
            "verified": verified,
            "verified_on": adr.get("verified_on") if verified else None,
            "currency": adr.get("currency"),
            "listing": adr.get("listing"),
            "ratio": adr.get("ratio"),
        })
        if not verified:
            info["warnings"].append(
                f"{local}: ADR {adr['us_ticker']} is not verified; used for analysis only, "
                "no Capital.com epic until it is checked"
            )
        return info

    if info["reason"] is None:
        info.update({
            "tier": "native",
            "polygon_ticker": to_polygon(ticker),
            "capital_epic": to_capital_epic(ticker),
            "capital_epic_verified": capital_epic_verified(ticker),
            "verified": True,
        })
        return info

    etf = proxy_etf(ticker)
    if etf:
        info.update({"tier": "proxy", "proxy_etf": etf})
    return info


def options_underlying(ticker) -> str | None:
    """Symbol whose US options represent ``ticker`` itself (own or ADR), or None."""
    instrument = resolve_instrument(ticker)
    if instrument["tier"] in ("native", "adr"):
        return instrument["analysis_ticker"]
    return None


def options_exclusion(ticker) -> dict | None:
    """Exclusion entry for scripts that need the ticker's own options (GEX, VIX).

    None for ``native`` and ``adr`` tickers. Otherwise ``{"ticker", "reason",
    "tier", "proxy_etf"}``; the proxy ETF is a reference only and is not mixed
    into the portfolio figures.
    """
    instrument = resolve_instrument(ticker)
    if instrument["tier"] in ("native", "adr"):
        return None
    reason = instrument["reason"] or "no US-listed options"
    if instrument["proxy_etf"]:
        reason += (
            f"; no ADR, proxy {instrument['proxy_etf']} listed for reference only "
            "(not included in portfolio figures)"
        )
    elif instrument["local"]:
        reason += "; no ADR and no proxy ETF"
    return {
        "ticker": instrument["local"],
        "reason": reason,
        "tier": instrument["tier"],
        "proxy_etf": instrument["proxy_etf"],
    }


def adr_warnings(tickers) -> list[str]:
    """Resolver warnings (unverified ADRs) for the given tickers."""
    out = []
    for ticker in tickers or []:
        out.extend(resolve_instrument(ticker)["warnings"])
    return out


def _env_float(name):
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if value != value or value < 0:
        return None
    return value


def no_options_weight_cap(target_weight, factor=None, absolute=None):
    """Capped target weight for tier ``none``: ``factor`` x target, and <= ``absolute``.

    Defaults come from ``NO_OPTIONS_WEIGHT_CAP_FACTOR`` (0.5) and
    ``NO_OPTIONS_WEIGHT_CAP`` (unset = no absolute cap).
    """
    if target_weight is None:
        return None
    target = float(target_weight)
    if target != target:
        return target
    if factor is None:
        factor = _env_float(NO_OPTIONS_CAP_FACTOR_ENV)
    if factor is None:
        factor = DEFAULT_NO_OPTIONS_CAP_FACTOR
    if absolute is None:
        absolute = _env_float(NO_OPTIONS_CAP_ENV)
    capped = target * min(float(factor), 1.0)
    if absolute is not None:
        capped = min(capped, float(absolute))
    return capped


def dividend_yield_from_info(info, max_yield=0.25):
    """Dividend yield as a fraction (0.0045 = 0.45%) from a yfinance ``.info``.

    ``trailingAnnualDividendYield`` and ``yield`` (ETFs) come as fractions.
    ``dividendYield`` comes as a percent since Yahoo changed the field in 2025
    (0.45 = 0.45%), so guessing by size misreads yields below 1% (or 0.25%) as
    fractions. Returns None when no field gives a usable value.
    """
    info = info or {}
    candidates = (
        ("trailingAnnualDividendYield", 1.0),
        ("yield", 1.0),
        ("dividendYield", 100.0),
    )
    for key, scale in candidates:
        raw = info.get(key)
        if raw is None or isinstance(raw, bool):
            continue
        try:
            value = float(raw) / scale
        except (TypeError, ValueError):
            continue
        if value != value or value < 0:  # NaN o negativo
            continue
        if value <= max_yield:
            return value
    return None
