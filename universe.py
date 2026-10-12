"""Candidate universe for drawdown_rotation.py: top S&P 500 and NASDAQ names by market cap.

Same method as quadratic_utility.py in AM-PM-Architecture: scrape the
stockanalysis.com lists (S&P 500 with slickcharts.com as fallback, NASDAQ),
parse the "Market Cap" column ($3.5T, 812B...) and sort by it.

On top of that, ``build_universe`` makes the two lists add up to n_sp500 +
n_nasdaq UNIQUE names: the S&P list is taken first in market-cap order, then
the NASDAQ list fills its quota skipping names already taken, still in
market-cap order. Excluded tickers (the portfolio's own holdings) are skipped
the same way, and only one share class per company is kept (GOOGL, not GOOG).

A custom list can replace the indices or be added to them (``mode``).
"""

from __future__ import annotations

import io
import re

import numpy as np
import pandas as pd

SP500_URLS = (
    "https://stockanalysis.com/list/sp-500-stocks/",
    "https://www.slickcharts.com/sp500",
)
NASDAQ_URLS = ("https://stockanalysis.com/list/nasdaq-stocks/",)
USER_AGENT = "Mozilla/5.0 (compatible; PortfolioBot/1.0)"

# Used only when every scrape fails, already in market-cap order (approximate).
SP500_FALLBACK = [
    "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "BRK-B", "JPM",
    "WMT", "LLY", "ORCL", "V", "MA", "NFLX", "XOM", "COST", "JNJ", "PLTR",
    "HD", "ABBV", "BAC", "PG", "AMD", "UNH", "GE", "KO", "CSCO", "CVX",
    "IBM", "WFC", "MS", "PM", "CAT", "GS", "TMUS", "AXP", "MU", "ABT",
    "CRM", "MRK", "RTX", "MCD", "PEP", "LIN", "DIS", "UBER", "TMO", "INTU",
]
NASDAQ_FALLBACK = [
    "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "NFLX", "COST",
    "PLTR", "ASML", "AMD", "CSCO", "AZN", "TMUS", "MU", "SHOP", "PEP", "LIN",
    "APP", "INTU", "PDD", "LRCX", "AMAT", "QCOM", "ISRG", "BKNG", "AMGN", "INTC",
    "KLAC", "ARM", "TXN", "GILD", "ADBE", "PANW", "CRWD", "HON", "ADP", "MELI",
    "CMCSA", "VRTX", "ADI", "SBUX", "CEG", "MSTR", "DASH", "CDNS", "ORLY", "SNPS",
]

UNIVERSE_MODES = ("indices", "custom", "both")


def parse_market_cap(value) -> float:
    """``$3.5T`` / ``812.3B`` / ``950M`` -> dollars; NaN when it does not parse."""
    text = str(value).strip().upper().replace(",", "")
    match = re.match(r"^\$?\s*([0-9]*\.?[0-9]+)\s*([TBMK]?)$", text)
    if not match:
        return np.nan
    number, suffix = match.groups()
    return float(number) * {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3, "": 1.0}[suffix]


def clean_symbol_table(table: pd.DataFrame) -> pd.DataFrame:
    """Normalize a scraped list: ``symbol`` column, Yahoo-style class shares
    (BRK.B -> BRK-B), no index rows, sorted by market cap when the column exists.

    Adds ``market_cap_usd`` (NaN when missing) and ``company`` (the name column,
    when the table has one)."""
    tbl = table.copy()
    tbl.columns = [str(c).strip().lower().replace(" ", "_") for c in tbl.columns]
    symbol_col = "symbol" if "symbol" in tbl.columns else tbl.columns[1]
    tbl = tbl.rename(columns={symbol_col: "symbol"})
    sym = tbl["symbol"].astype(str).str.strip()
    tbl = tbl[
        tbl["symbol"].notna()
        & ~sym.str.contains(r"\^|\$", regex=True)
        & (sym.str.len() >= 1)
        & (sym.str.len() <= 6)
        & ~sym.str.match(r"^[0-9]")
    ].copy()
    tbl["symbol"] = tbl["symbol"].astype(str).str.strip().str.upper().str.replace(".", "-", regex=False)

    name_col = next((c for c in ("company_name", "company", "name") if c in tbl.columns), None)
    tbl["company"] = tbl[name_col].astype(str).str.strip() if name_col else ""
    if "market_cap" in tbl.columns:
        tbl["market_cap_usd"] = tbl["market_cap"].apply(parse_market_cap)
        if tbl["market_cap_usd"].notna().any():
            tbl = tbl.sort_values("market_cap_usd", ascending=False, kind="stable", na_position="last")
    else:
        tbl["market_cap_usd"] = np.nan
    return tbl[["symbol", "company", "market_cap_usd"]].reset_index(drop=True)


def scrape_table(url: str, session=None, timeout: float = 20.0):
    """First HTML table of ``url`` as a DataFrame, or None (the error is printed)."""
    import requests

    getter = session or requests
    try:
        resp = getter.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        resp.raise_for_status()
        tables = pd.read_html(io.StringIO(resp.text))
    except Exception as exc:  # noqa: BLE001 - any failure falls back to the next source
        print(f"[universe] could not read {url}: {exc}")
        return None
    return tables[0] if tables else None


def index_constituents(urls, fallback, label: str, scraper=scrape_table) -> tuple[pd.DataFrame, str]:
    """Market-cap-sorted list of an index: the first URL that answers, else ``fallback``.

    Returns ``(table, source)`` where ``source`` is the URL used or ``"fallback"``."""
    for url in urls:
        raw = scraper(url)
        if raw is None or len(raw) == 0:
            continue
        try:
            table = clean_symbol_table(raw)
        except Exception as exc:  # noqa: BLE001
            print(f"[universe] {label}: unexpected table at {url} ({exc})")
            continue
        if not table.empty:
            return table, url
    print(f"[universe] {label}: every source failed; using the built-in fallback list.")
    table = pd.DataFrame({"symbol": list(fallback), "company": "", "market_cap_usd": np.nan})
    return table, "fallback"


def _company_key(row) -> str:
    name = str(row.get("company") or "").strip().lower()
    if name and name != "nan":
        # "Alphabet Inc." for GOOGL and GOOG: one company, two share classes.
        return re.sub(r"[^a-z0-9]+", " ", name).strip()
    return f"symbol:{row['symbol']}"


def take_top(table: pd.DataFrame, n: int, taken: set, companies: set, exclude: set) -> list[dict]:
    """First ``n`` rows (market-cap order) not in ``taken``/``exclude`` and of a new company."""
    picked = []
    if n <= 0:
        return picked
    for _, row in table.iterrows():
        symbol = row["symbol"]
        company = _company_key(row)
        if symbol in taken or symbol in exclude or company in companies:
            continue
        picked.append({"ticker": symbol, "company": row.get("company") or "",
                       "market_cap_usd": row.get("market_cap_usd")})
        taken.add(symbol)
        companies.add(company)
        if len(picked) >= n:
            break
    return picked


def normalize_tickers(tickers) -> list[str]:
    out = []
    for ticker in tickers or []:
        text = str(ticker).strip().upper().replace(".", "-")
        if text and text not in out:
            out.append(text)
    return out


def build_universe(n_sp500: int = 30, n_nasdaq: int = 30, mode: str = "indices",
                   custom_tickers=None, exclude=None, scraper=scrape_table) -> dict:
    """Unique candidate tickers for the rotation.

    ``mode``: "indices" (top S&P 500 + top NASDAQ), "custom" (only
    ``custom_tickers``) or "both" (indices, then the custom names not already in).
    ``exclude``: tickers that can never be candidates (current holdings).

    Returns ``{"tickers", "rows", "sources", "shortfall"}``; ``rows`` keeps the
    origin ("sp500" / "nasdaq" / "custom") and market cap of every ticker.
    """
    if mode not in UNIVERSE_MODES:
        raise ValueError(f"universe mode must be one of {UNIVERSE_MODES}, got {mode!r}")
    exclude = set(normalize_tickers(exclude))
    taken, companies = set(), set()
    rows, sources = [], {}
    shortfall = {}

    if mode in ("indices", "both"):
        sp_table, sources["sp500"] = index_constituents(SP500_URLS, SP500_FALLBACK, "S&P 500", scraper)
        nq_table, sources["nasdaq"] = index_constituents(NASDAQ_URLS, NASDAQ_FALLBACK, "NASDAQ", scraper)
        for origin, table, n in (("sp500", sp_table, n_sp500), ("nasdaq", nq_table, n_nasdaq)):
            picked = take_top(table, n, taken, companies, exclude)
            rows += [dict(item, origin=origin) for item in picked]
            if len(picked) < n:
                shortfall[origin] = n - len(picked)

    if mode in ("custom", "both"):
        sources["custom"] = "user list"
        for ticker in normalize_tickers(custom_tickers):
            if ticker in taken or ticker in exclude:
                continue
            taken.add(ticker)
            rows.append({"ticker": ticker, "company": "", "market_cap_usd": np.nan, "origin": "custom"})

    return {
        "tickers": [row["ticker"] for row in rows],
        "rows": rows,
        "sources": sources,
        "shortfall": shortfall,
    }
