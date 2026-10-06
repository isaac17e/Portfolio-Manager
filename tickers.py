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
"""

from __future__ import annotations

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

# Capital.com epics verified against the Capital.com API on 2026-10-06, keyed by
# the Yahoo form of the ticker. ``RY`` is the NYSE listing quoted in USD:
# Capital.com has no TSX/CAD line for Royal Bank of Canada.
_CAPITAL_VERIFIED_ON = "2026-10-06"
_CAPITAL_VERIFIED = {
    "BRK-B": {"epic": "BRKB"},  # "BRK.B" does not exist; "BRKb" -> error.not-found.epic
    "RY.TO": {"epic": "RY", "currency": "USD", "listing": "NYSE"},
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
