"""Shared portfolio input and signal output for the Portfolio-Manager scripts.

Contract: pipeline JSON v1, section 4 (signals). Section 1 describes the
portfolio file this module reads. Writes are atomic and never raise when the
output directory cannot be created or written.

Fills formats (EXECUTIONS_DIR, written by the executor, ARES)
-------------------------------------------------------------
Buy fills, ``fills_<optimizer>_<run_ts stamp>.json``: ``schema_version`` 1,
``signal_run_ts`` (the entry signal they confirm), ``executed_ts`` and
``fills[]`` with ``ticker``, ``action`` "BUY", ``filled_weight``, ``filled_qty``,
``price``, ``deal_id``, ``status``. See ``load_portfolio_fills``.

Sell fills, ``sell_fills_<optimizer>_<stamp>.json`` (design: no real file
existed when this was written). The executor records the sales that
``drawdown_rotation`` asks for here, never in the buy file. Same top level
as the buy file except that it names the portfolio instead of a signal::

    {"schema_version": 1, "script": "drawdown_rotation",
     "portfolio_optimizer": "minimum_variance",
     "portfolio_run_ts": "2026-10-08T11:05:16-05:00",
     "account": "...", "account_id": "...",
     "executed_ts": "...", "written_ts": "...",
     "fills": [{"ticker": "GLD", "action": "SELL", "filled_qty": 10,
                "filled_weight": 0.06, "price": 180.0, "deal_id": "abc",
                "status": "filled", "fill_ts": "...", "reason": "ROTACION_SALIDA"}]}

``filled_qty`` and ``filled_weight`` are POSITIVE amounts sold. The reader is
tolerant: a negative ``filled_qty``, or ``side: "SELL"``, also means a sale, and
the absolute value is what was sold. There may be several sell files per
portfolio (one per executed rotation): all of them are read. A file belongs to
the portfolio when ``portfolio_optimizer`` matches and ``portfolio_run_ts``
gives the same stamp as the portfolio's; when the file has no ``portfolio_run_ts``
the ``<stamp>`` of its name must be the portfolio's stamp. Only statuses
``filled`` / ``partial`` / ``partially_filled`` count.

``load_portfolio_holdings`` combines both kinds into the NET held quantity per
ticker (bought - sold, never below 0).

Holdings snapshot, ``holdings_<optimizer>_<stamp>.json`` (see ``current_holdings``)
-----------------------------------------------------------------------------------
Written by the executor from the broker's positions::

    {"schema_version": 1, "portfolio_run_ts": "2026-10-08T12:12:53-05:00",
     "portfolio_optimizer": "quadratic_utility", "account_id": "...",
     "as_of": "2026-10-14T15:58:12-04:00", "source": "capital_positions",
     "positions": [{"ticker": "AVGO", "qty": 14.65, "price": 412.3,
                    "market_value": 6040.2}]}

``as_of`` carries a UTC offset. ``current_holdings`` uses the snapshot only when it is at
most one NYSE session old, else the net fills, else the portfolio file's weights.

Cumulative buy fills (format change, backward compatible)
---------------------------------------------------------
The entry runs over several days (tranches). The buy file of a portfolio is
CUMULATIVE: ``write_portfolio_fills`` merges each new tranche into the existing
``fills_<optimizer>_<stamp>.json`` instead of overwriting it. The top-level fields
are those of the newest tranche (``signal_run_ts``, ``executed_ts``, ...), ``fills[]``
holds the fills of EVERY tranche (deduplicated by ``ticker`` + ``action`` +
``deal_id`` + ``fill_ts``), each carrying its own ``signal_run_ts`` (the tranche it
confirms), and ``tranches[]`` lists ``{"signal_run_ts", "executed_ts"}`` oldest
first. A single-day file written the old way is still valid: its fills have no
per-fill ``signal_run_ts`` and count as belonging to the file's ``signal_run_ts``.

The reader (``load_portfolio_fill_docs``) does not rely on the writer: net holdings
add up the fills of ALL ``fills_<optimizer>_<stamp>*.json`` / ``*.bak`` files of the
portfolio (a day-1 file that was overwritten and kept as ``.bak`` still counts), with
the same dedupe, so a fill present in two files counts once.

Manual overrides, ``manual_overrides.json`` (written by ARES, read by every script)
-----------------------------------------------------------------------------------
When Isaac approves or rejects a replacement / rotation that differs from the one the
pipeline proposed, ARES records it in ``<PIPELINE_DIR>/state/manual_overrides.json``
(``MANUAL_OVERRIDES_FILE`` overrides the path). One file for all portfolios, keyed like
the fills files (``<optimizer>_<run_ts stamp>``, see ``portfolio_key``)::

    {"schema_version": 1, "updated_ts": "2026-10-09T10:02:11-05:00",
     "portfolios": {"quadratic_utility_20261008T121253": {
       "account_id": "ACC-123",
       "overrides": [{
         "id": "ovr-20261009-001",
         "ts": "2026-10-09T10:01:40-05:00",
         "action": "replace",
         "replaced_ticker": "FTNT", "chosen_ticker": "MRK", "target_weight": 0.0462,
         "source_script": "drawdown_rotation", "approved_by": "isaac",
         "fills": ["deal-123"], "note": "Isaac prefers MRK over FTNT"}]}}}

Entry fields: ``id`` (unique within the portfolio), ``ts`` (ISO-8601 WITH a UTC offset),
``action``, ``replaced_ticker``, ``chosen_ticker``, ``target_weight`` (portfolio weight
as a fraction, same units as ``target_weight`` in the signals), ``approved_by`` (all
required) and ``source_script``, ``fills`` (deal ids), ``note`` (optional). Per action:

=========  ===============  ===============  ===============  ======================================
action     replaced_ticker  chosen_ticker    target_weight    effect
=========  ===============  ===============  ===============  ======================================
replace    required         required (!=)    required (0, 1]  replaced never BUY; chosen target set
add        null             required         required (0, 1]  chosen target set
reject     required         null             null (or 0)      ticker (the rejected proposal) never BUY
remove     required         null             null (or 0)      ticker taken out; never BUY
=========  ===============  ===============  ===============  ======================================

Entries are replayed oldest ``ts`` first (file order breaks ties); the latest word on a
ticker wins, so an ``add`` after a ``remove`` brings it back. ``load_manual_overrides``
reads it (never raises), ``validate_manual_overrides`` lists every problem with its path,
``effective_targets`` merges it with the rotation state (precedence: manual overrides >
rotation ``target_overrides`` / entry ``pending_targets`` > portfolio file), and
``buy_gate`` / ``apply_buy_gate`` decide, per BUY, between ``BUY``, dropped (blocked) and
``REQUIRES_VERIFICATION``. A missing file, or no section for the portfolio, changes
nothing. An invalid file is warned about, never crashes a cycle, and the tickers it may
affect get ``REQUIRES_VERIFICATION`` instead of BUY (see ``load_manual_overrides``).

``REQUIRES_VERIFICATION`` is emitted in place of ``BUY``: ``action`` and ``status`` are
both ``"REQUIRES_VERIFICATION"``, ``verification_reason`` says why and ``original_action``
is ``"BUY"``. The executor must NOT place an order for it: it asks Isaac, and on approval
records an ``add`` / ``replace`` override (or ``reject`` / ``remove``); the next run
emits a normal BUY (or nothing).

Entry phase (days 1..5 of a portfolio)
--------------------------------------
``entry_phase_info`` counts NYSE sessions from day 1 of the portfolio's entry
(``entry_start_date`` in the entry state file; older state files fall back to the
earliest fill date, then the portfolio ``run_ts`` date). During days 1..5
``drawdown_rotation`` only PAUSES (see ``load_pause_mark``) and ``run_cycle --weekly``
skips ``active_management``.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

BOGOTA = ZoneInfo("America/Bogota")
SCHEMA_VERSION = 1
DEFAULT_PORTFOLIO_FILE = "/workspace/pipeline/portfolio/portfolio_latest.json"
DEFAULT_SIGNALS_DIR = "/workspace/pipeline/signals"
DEFAULT_EXECUTIONS_DIR = "/workspace/pipeline/executions"
_APPLIED_FILL_STATUSES = {"filled", "partial", "partially_filled"}
_WEIGHT_UNIT = 1_000_000
_ZERO_WEIGHT = 1e-6

# Portfolio horizon (contract section 1: horizon_days, horizon_end,
# params.horizon_months). run_cycle passes each step its horizon in calendar
# days through HORIZON_ENV; standalone runs read it from the portfolio file.
HORIZON_ENV = "PORTFOLIO_HORIZON_DAYS"
# Shortest option expiry (calendar days) any script reads for the horizon.
# Below a week the chain is dominated by expiry-week gamma and pin effects.
MIN_OPTION_DAYS = 7
_DAYS_PER_MONTH = 30.44


def _now_bogota() -> datetime:
    return datetime.now(BOGOTA).replace(microsecond=0)


def _warn(message: str) -> None:
    print(f"[pipeline_io] {message}")


def resolve_risk_free_rate(default, env=None):
    """Annual risk-free rate (decimal): ``RISK_FREE_RATE`` if set, else ``default``.

    Mirrors AM-PM-Architecture's helper. Read it once at script start. A value
    that is not a number, or outside [0, 0.5), raises ``ValueError``.
    """
    raw = (os.environ if env is None else env).get("RISK_FREE_RATE")
    if raw is None or not str(raw).strip():
        return float(default)
    try:
        rate = float(str(raw).strip())
    except ValueError:
        raise ValueError(
            f"invalid RISK_FREE_RATE: {raw!r}. Use an annual decimal, e.g. 0.052."
        ) from None
    if not math.isfinite(rate) or not 0.0 <= rate < 0.5:
        raise ValueError(
            f"RISK_FREE_RATE out of range: {raw!r}. Must satisfy 0 <= rf < 0.5 "
            "(annual decimal: 0.052 is 5.2%)."
        )
    return rate


def cycle_today() -> date:
    """Today in America/Bogota, or ``CYCLE_DATE`` (YYYY-MM-DD) when set.

    ``run_cycle.py`` exports its ``--date`` as ``CYCLE_DATE`` so the steps agree
    with the orchestrator on the day (and tests are deterministic).
    """
    raw = os.environ.get("CYCLE_DATE")
    if raw is None or not raw.strip():
        return datetime.now(BOGOTA).date()
    try:
        return datetime.strptime(raw.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"invalid CYCLE_DATE: {raw!r}. Use YYYY-MM-DD.") from None


def _fallback_result(fallback, reason: str) -> dict:
    _warn(f"{reason} Using hardcoded portfolio fallback.")
    weights = {}
    try:
        for key, value in dict(fallback).items():
            weights[str(key)] = float(value)
    except (TypeError, ValueError) as exc:
        _warn(f"Hardcoded fallback is not a ticker->weight mapping ({exc}).")
        weights = fallback
    return {
        "weights": weights,
        "portfolio_source": "hardcoded_fallback",
        "portfolio_run_ts": None,
        "portfolio_optimizer": None,
        "horizon_days": None,
        "horizon_end": None,
        "horizon_months": None,
    }


def _renormalize_weights(raw: dict) -> dict:
    """Drop dust weights and rescale so 6-decimal-place weights sum to 1."""
    if not isinstance(raw, dict) or not raw:
        raise ValueError("weights must be a non-empty object")

    cleaned = []
    seen = set()
    for key, value in raw.items():
        ticker = str(key).strip()
        if not ticker:
            raise ValueError("weights contain an empty ticker")
        if ticker in seen:
            raise ValueError(f"duplicate ticker {ticker}")
        seen.add(ticker)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"weight for {ticker} is not a number")
        number = float(value)
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"weight for {ticker} must be a finite number >= 0")
        if number >= _ZERO_WEIGHT:
            cleaned.append((ticker, number))

    if not cleaned:
        raise ValueError("weights have no positive holdings after dropping zeros")

    total = sum(value for _, value in cleaned)
    units = []
    for ticker, value in cleaned:
        share = Decimal(value) / Decimal(total) * Decimal(_WEIGHT_UNIT)
        unit = int(share.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        if unit > 0:
            units.append([ticker, unit])
    if not units:
        raise ValueError("weights round to zero")

    drift = _WEIGHT_UNIT - sum(unit for _, unit in units)
    guard = 0
    while drift != 0:
        guard += 1
        if guard > _WEIGHT_UNIT:
            raise ValueError("could not make weights sum to 1")
        step = 1 if drift > 0 else -1
        ranked = sorted(range(len(units)), key=lambda i: (-units[i][1], units[i][0]))
        moved = False
        for index in ranked:
            if units[index][1] + step > 0:
                units[index][1] += step
                drift -= step
                moved = True
                break
        if not moved:
            raise ValueError("could not make weights sum to 1")

    units.sort(key=lambda item: (-item[1], item[0]))
    return {ticker: unit / _WEIGHT_UNIT for ticker, unit in units}


def load_portfolio(fallback) -> dict:
    """Read PORTFOLIO_FILE, validate weights, and return weights plus metadata.

    ``fallback`` is the script's hardcoded ``{ticker: weight}`` dict. It is
    returned unchanged (aside from a shallow copy) when the file is missing or
    invalid. On success, weights are dust-filtered and renormalized to 1.
    """
    path = os.environ.get("PORTFOLIO_FILE", DEFAULT_PORTFOLIO_FILE)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        return _fallback_result(fallback, f"Portfolio file not found ({path}).")
    except OSError as exc:
        return _fallback_result(fallback, f"Could not read portfolio file ({path}): {exc}.")
    except json.JSONDecodeError as exc:
        return _fallback_result(fallback, f"Portfolio file is not valid JSON ({path}): {exc}.")

    if not isinstance(payload, dict):
        return _fallback_result(fallback, f"Portfolio file is not a JSON object ({path}).")

    version = payload.get("schema_version", SCHEMA_VERSION)
    if version != SCHEMA_VERSION:
        return _fallback_result(
            fallback, f"Unsupported portfolio schema_version {version!r} ({path})."
        )

    try:
        weights = _renormalize_weights(payload.get("weights"))
    except ValueError as exc:
        return _fallback_result(fallback, f"Invalid portfolio weights ({path}): {exc}.")

    run_ts = payload.get("run_ts")
    optimizer = payload.get("optimizer")
    horizon = portfolio_horizon_fields(payload)
    end = horizon["horizon_end"]
    return {
        "weights": weights,
        "portfolio_source": path,
        "portfolio_run_ts": run_ts if isinstance(run_ts, str) and run_ts else None,
        "portfolio_optimizer": optimizer if isinstance(optimizer, str) and optimizer else None,
        "horizon_days": horizon["horizon_days"],
        "horizon_end": end.isoformat() if end else None,
        "horizon_months": horizon["horizon_months"],
    }


def _positive_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number > 0 else None


def _iso_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _add_months(start: date, months: float) -> date:
    whole = int(months)
    if whole != months:
        return start + timedelta(days=round(months * _DAYS_PER_MONTH))
    return start + relativedelta(months=whole)


def portfolio_horizon_fields(portfolio) -> dict:
    """Horizon fields of a portfolio payload, or of a ``load_portfolio`` result.

    Returns ``horizon_days`` (int or None), ``horizon_end`` (date or None),
    ``horizon_months`` (number or None; top level or ``params.horizon_months``)
    and ``run_date`` (date of ``run_ts`` / ``portfolio_run_ts`` or None).
    Invalid values are treated as missing.
    """
    portfolio = portfolio if isinstance(portfolio, dict) else {}
    days = _positive_number(portfolio.get("horizon_days"))
    params = portfolio.get("params") if isinstance(portfolio.get("params"), dict) else {}
    months = _positive_number(portfolio.get("horizon_months"))
    if months is None:
        months = _positive_number(params.get("horizon_months"))
    run_ts = portfolio.get("run_ts") or portfolio.get("portfolio_run_ts")
    run_date = None
    if isinstance(run_ts, str) and run_ts.strip():
        try:
            run_date = datetime.fromisoformat(re.sub(r"Z$", "+00:00", run_ts.strip())).date()
        except ValueError:
            run_date = None
    return {
        "horizon_days": int(round(days)) if days is not None else None,
        "horizon_end": _iso_date(portfolio.get("horizon_end")),
        "horizon_months": months,
        "run_date": run_date,
    }


def portfolio_horizon_days(portfolio, today=None, mode: str = "remaining") -> int | None:
    """Calendar days of the portfolio horizon, or None when the file has none.

    ``mode="full"``: the whole term (``horizon_days``, else ``horizon_end``
    minus the run date, else ``horizon_months``). ``mode="remaining"``: days
    from ``today`` (default ``cycle_today()``) to ``horizon_end``; the end is
    derived from the run date plus ``horizon_days`` / ``horizon_months`` when
    ``horizon_end`` is missing, and without any end date it is the full term.
    The remaining value can be zero or negative after the horizon has passed.
    """
    if mode not in ("full", "remaining"):
        raise ValueError(f"mode must be 'full' or 'remaining', got {mode!r}")
    info = portfolio_horizon_fields(portfolio)
    run_date, end = info["run_date"], info["horizon_end"]
    if end is None and run_date is not None:
        if info["horizon_days"] is not None:
            end = run_date + timedelta(days=info["horizon_days"])
        elif info["horizon_months"] is not None:
            end = _add_months(run_date, info["horizon_months"])

    full = info["horizon_days"]
    if full is None and end is not None and run_date is not None and end > run_date:
        full = (end - run_date).days
    if full is None and info["horizon_months"] is not None:
        full = int(round(info["horizon_months"] * _DAYS_PER_MONTH))

    if mode == "full":
        return full
    if end is None:
        return full
    today = _iso_date(today) or cycle_today()
    return (end - today).days


def resolve_horizon(portfolio_meta, default_days, mode: str = "remaining", today=None,
                    env=None, min_days: int = MIN_OPTION_DAYS) -> dict:
    """Horizon a script works with, in calendar days, with where it came from.

    Order: ``PORTFOLIO_HORIZON_DAYS`` (set by run_cycle), then the portfolio
    file (``portfolio_horizon_days`` with ``mode``), then ``default_days``.
    ``days`` is never below ``min_days``. The dict goes into each signal's
    ``data["horizon"]``: ``days``, ``source`` ("portfolio" or "default"),
    ``via`` ("env", "file" or None), ``mode``, ``raw_days`` (before the floor),
    ``min_days``, ``floored``, ``default_days`` and ``horizon_end``.
    """
    environ = os.environ if env is None else env
    raw, source, via = None, "default", None
    text = environ.get(HORIZON_ENV)
    if text is not None and str(text).strip():
        try:
            number = float(str(text).strip())
        except ValueError:
            number = None
        if number is not None and math.isfinite(number):
            raw, source, via = int(round(number)), "portfolio", "env"
        else:
            _warn(f"Ignoring invalid {HORIZON_ENV}={text!r}.")
    if raw is None:
        from_file = portfolio_horizon_days(portfolio_meta, today=today, mode=mode)
        if from_file is not None:
            raw, source, via = int(from_file), "portfolio", "file"
    if raw is None:
        raw = int(round(default_days))
    days = max(raw, int(min_days))
    end = portfolio_horizon_fields(portfolio_meta)["horizon_end"]
    return {
        "days": days,
        "source": source,
        "via": via,
        "mode": mode,
        "raw_days": raw,
        "min_days": int(min_days),
        "floored": days != raw,
        "default_days": int(round(default_days)),
        "horizon_end": end.isoformat() if end else None,
    }


def pick_expiration(expirations, today, target_days, min_days: int = MIN_OPTION_DAYS):
    """Expiry closest to ``today + target_days`` among those ``>= min_days`` out.

    ``expirations`` are dates or YYYY-MM-DD strings. Returns ``(expiry, fallback)``.
    When no expiry clears the floor, the one closest to the target is returned
    with ``fallback=True``; an empty list gives ``(None, False)``. Ties go to
    the earlier expiry, as in the scripts' previous selection.
    """
    today = _iso_date(today)
    parsed = sorted({d for d in (_iso_date(e) for e in expirations or []) if d is not None})
    parsed = [d for d in parsed if d >= today]
    if not parsed:
        return None, False
    target = today + timedelta(days=max(int(round(target_days)), int(min_days)))
    eligible = [d for d in parsed if (d - today).days >= int(min_days)]
    pool = eligible or parsed
    return min(pool, key=lambda d: abs((d - target).days)), not eligible


def _is_nan(value) -> bool:
    if isinstance(value, float):
        return not math.isfinite(value)
    if np is not None and isinstance(value, np.floating):
        return not math.isfinite(float(value))
    if pd is None:
        return False
    if value is pd.NA or value is pd.NaT:
        return True
    if isinstance(value, (str, bytes, bool, int, datetime, date, list, tuple, dict)):
        return False
    if np is not None and isinstance(value, (np.ndarray, np.integer, np.bool_)):
        return False
    try:
        missing = pd.isna(value)
    except (TypeError, ValueError):
        return False
    return missing is True or (np is not None and missing is np.True_)


def to_jsonable(value):
    """Convert numpy, pandas and non-finite floats so ``json`` can emit null."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, float):
        return None if not math.isfinite(value) else value
    if isinstance(value, (datetime, date)) or (
        pd is not None and isinstance(value, pd.Timestamp)
    ):
        if _is_nan(value):
            return None
        return value.isoformat()

    if np is not None:
        if isinstance(value, np.ndarray):
            return [to_jsonable(item) for item in value.tolist()]
        if isinstance(value, np.bool_):
            return bool(value)
        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            number = float(value)
            return None if not math.isfinite(number) else number

    if pd is not None:
        if isinstance(value, pd.DataFrame):
            frame = value.reset_index() if value.index.name else value
            return [to_jsonable(row) for row in frame.to_dict(orient="records")]
        if isinstance(value, pd.Series):
            return {str(key): to_jsonable(item) for key, item in value.items()}

    if _is_nan(value):
        return None
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]

    _warn(f"Converted non-JSON value of type {type(value).__name__} with str().")
    return str(value)


def _atomic_write(path: str, text: str) -> None:
    temporary = path + ".tmp"
    try:
        with open(temporary, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(temporary, path)
    except Exception:
        try:
            os.remove(temporary)
        except OSError:
            pass
        raise


def export_signals(script: str, data, portfolio_meta, warnings=None) -> str | None:
    """Write ``<script>.json`` and a timestamped copy. Returns the latest path.

    The directory is ``resolve_signals_dir(portfolio_meta)``: one subfolder per
    portfolio by default (see that function for the env switches).

    Returns None, after a warning, when the directory cannot be created or
    written. Other export errors are also warned and swallowed so a portfolio
    run is never aborted by the signal file.

    ``warnings``, when not None, is written as a top-level array. Omit it to
    keep the original envelope (callers that have nothing to flag).
    """
    out_dir = resolve_signals_dir(portfolio_meta)
    try:
        os.makedirs(out_dir, exist_ok=True)
        run_at = _now_bogota()
        meta = portfolio_meta or {}
        envelope = {
            "schema_version": SCHEMA_VERSION,
            "script": script,
            "run_ts": run_at.isoformat(),
            "portfolio_source": meta.get("portfolio_source"),
            "portfolio_run_ts": meta.get("portfolio_run_ts"),
            "portfolio_optimizer": meta.get("portfolio_optimizer"),
            "weights_used": to_jsonable(meta.get("weights") or {}),
            "data": to_jsonable(data),
        }
        if warnings is not None:
            envelope["warnings"] = to_jsonable(list(warnings))
        text = json.dumps(envelope, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        latest = os.path.join(out_dir, f"{script}.json")
        stamped = os.path.join(out_dir, f"{script}_{run_at.strftime('%Y%m%dT%H%M%S')}.json")
        _atomic_write(latest, text)
        _atomic_write(stamped, text)
        return latest
    except Exception as exc:
        _warn(
            f"Could not write signal file for {script} under {out_dir}: {exc}. "
            "Continuing without the JSON export."
        )
        return None


def executions_dir() -> str:
    return os.environ.get("EXECUTIONS_DIR", DEFAULT_EXECUTIONS_DIR)


def locate_fills_file(script: str = "entry_signal_tool", directory: str | None = None) -> str | None:
    """Prefer ``<script>_fills.json``; otherwise the newest ``fills_*.json``."""
    directory = executions_dir() if directory is None else directory
    named = os.path.join(directory, f"{script}_fills.json")
    if os.path.isfile(named):
        return named
    if not os.path.isdir(directory):
        return None
    try:
        names = os.listdir(directory)
    except OSError as exc:
        _warn(f"Could not list executions directory ({directory}): {exc}.")
        return None
    matches = []
    for name in names:
        if name.startswith("fills_") and name.endswith(".json"):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                matches.append(path)
    if not matches:
        return None
    matches.sort(key=lambda path: (os.path.getmtime(path), os.path.basename(path)))
    return matches[-1]


def _file_token(value) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", str(value).strip()).strip("_")


def run_ts_stamp(run_ts) -> str:
    """Portfolio ``run_ts`` as a file stamp, ``YYYYMMDDTHHMMSS``.

    Same stamp the portfolio writer uses for ``portfolio_<optimizer>_<stamp>.json``
    (local wall time of the ISO ``run_ts``, offset dropped). A value that is not
    ISO-8601 is reduced to ``[A-Za-z0-9_-]``.
    """
    text = str(run_ts).strip()
    try:
        return datetime.fromisoformat(re.sub(r"Z$", "+00:00", text)).strftime("%Y%m%dT%H%M%S")
    except ValueError:
        return _file_token(text)


def portfolio_key(portfolio_meta) -> str | None:
    """``<optimizer>_<run_ts stamp>`` for the portfolio, or None without both."""
    meta = portfolio_meta or {}
    optimizer = meta.get("portfolio_optimizer")
    run_ts = meta.get("portfolio_run_ts")
    if not optimizer or not run_ts:
        return None
    optimizer, stamp = _file_token(optimizer), run_ts_stamp(run_ts)
    if not optimizer or not stamp:
        return None
    return f"{optimizer}_{stamp}"


SIGNALS_DIR_EXACT_ENV = "SIGNALS_DIR_EXACT"
SIGNALS_PER_PORTFOLIO_ENV = "SIGNALS_PER_PORTFOLIO"
FALLBACK_SIGNALS_SUBDIR = "hardcoded_fallback"
ARTIFACTS_SUBDIR = "artifacts"
FIGURES_SUBDIR = "figures"
_OFF_VALUES = {"0", "false", "no", "off"}


def signals_base_dir(env=None) -> str:
    """``SIGNALS_OUT_DIR``, else ``DEFAULT_SIGNALS_DIR``: the parent of the portfolio folders."""
    env = os.environ if env is None else env
    return env.get("SIGNALS_OUT_DIR") or DEFAULT_SIGNALS_DIR


def per_portfolio_enabled(env=None) -> bool:
    """False only when ``SIGNALS_PER_PORTFOLIO`` is ``0`` (also false/no/off)."""
    env = os.environ if env is None else env
    return str(env.get(SIGNALS_PER_PORTFOLIO_ENV, "1")).strip().lower() not in _OFF_VALUES


def _portfolio_identity(portfolio) -> str | None:
    """``portfolio_key`` for a loaded meta (``portfolio_optimizer`` / ``portfolio_run_ts``)
    or a validated portfolio file (``optimizer`` / ``run_ts``)."""
    p = portfolio or {}
    return portfolio_key({
        "portfolio_optimizer": p.get("portfolio_optimizer") or p.get("optimizer"),
        "portfolio_run_ts": p.get("portfolio_run_ts") or p.get("run_ts"),
    })


def optimizer_history_path(portfolio, legacy_path: str, env=None) -> str:
    """``<name>_<optimizer><ext>`` next to ``legacy_path``: a history that spans many
    runs of the same optimizer (a new portfolio every cycle must not reset it), but
    must not mix optimizers. ``legacy_path`` itself in the flat legacy layout or
    when the portfolio has no optimizer."""
    p = portfolio or {}
    optimizer = _file_token(p.get("portfolio_optimizer") or p.get("optimizer") or "")
    if not optimizer or not uses_portfolio_layout(env):
        return legacy_path
    root, ext = os.path.splitext(legacy_path)
    return f"{root}_{optimizer}{ext}"


def portfolio_signals_dir(portfolio, base: str | None = None) -> str:
    """``<base>/<optimizer>_<YYYYMMDDTHHMMSS>``, or ``<base>/hardcoded_fallback``
    when the portfolio has no optimizer and run_ts. ``base`` defaults to
    ``signals_base_dir()``."""
    base = signals_base_dir() if base is None else base
    return os.path.join(base, _portfolio_identity(portfolio) or FALLBACK_SIGNALS_SUBDIR)


def resolve_signals_dir(portfolio=None, env=None) -> str:
    """Directory every script writes its signals to and run_cycle reads from.

    1. ``SIGNALS_DIR_EXACT`` set: used as is.
    2. else ``SIGNALS_PER_PORTFOLIO`` not ``0`` (the default): the
       ``portfolio_signals_dir`` under ``SIGNALS_OUT_DIR``.
    3. else the flat legacy folder ``SIGNALS_OUT_DIR``.
    """
    env = os.environ if env is None else env
    exact = env.get(SIGNALS_DIR_EXACT_ENV)
    if exact:
        return exact
    if per_portfolio_enabled(env):
        return portfolio_signals_dir(portfolio, signals_base_dir(env))
    return signals_base_dir(env)


def uses_portfolio_layout(env=None) -> bool:
    """True unless the flat legacy layout is in force (no exact dir and per-portfolio off)."""
    env = os.environ if env is None else env
    return bool(env.get(SIGNALS_DIR_EXACT_ENV)) or per_portfolio_enabled(env)


def artifact_path(portfolio, filename: str, legacy_dir: str, env=None) -> str:
    """Where a side output (HTML report, data JSON) of a script goes.

    ``<signals dir>/artifacts/<filename>``; in the flat legacy layout
    ``<legacy_dir>/<filename>``, where it used to be written."""
    if uses_portfolio_layout(env):
        return os.path.join(resolve_signals_dir(portfolio, env), ARTIFACTS_SUBDIR, filename)
    return os.path.join(legacy_dir, filename)


def prepare_artifact_path(path: str, fallback_dir: str) -> str:
    """Create the folder of ``path``. When that fails (read-only volume, bad
    permissions) warn and use ``fallback_dir`` instead: a report must never
    stop the step, whose signal is the product."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        return path
    except OSError as exc:
        _warn(f"Could not create the folder for {path}: {exc}. Using {fallback_dir}.")
        return os.path.join(fallback_dir, os.path.basename(path))


def default_figures_dir(portfolio=None, env=None) -> str:
    """``<signals dir>/figures``; ``<pipeline dir>/figures`` in the flat legacy layout."""
    if uses_portfolio_layout(env):
        return os.path.join(resolve_signals_dir(portfolio, env), FIGURES_SUBDIR)
    return os.path.join(pipeline_dir(), FIGURES_SUBDIR)


def announce_signals_dir(script: str, portfolio=None) -> str:
    """Print and return the resolved signals directory; called at the start of a script."""
    resolved = resolve_signals_dir(portfolio)
    print(f"[signals] {script}: output dir = {resolved}")
    return resolved


def portfolio_fills_path(portfolio_meta, directory: str | None = None) -> str | None:
    """``<EXECUTIONS_DIR>/fills_<optimizer>_<run_ts stamp>.json``, or None."""
    key = portfolio_key(portfolio_meta)
    if key is None:
        return None
    directory = executions_dir() if directory is None else directory
    return os.path.join(directory, f"fills_{key}.json")


def load_portfolio_fills(portfolio_meta, directory: str | None = None):
    """Read only the fills file of this portfolio, or return None. Never raises."""
    path = portfolio_fills_path(portfolio_meta, directory)
    if not path or not os.path.isfile(path):
        return None
    return _read_fills(path)


_FILL_SEPARATORS = "._-"


def _fills_candidates(portfolio_meta, directory: str | None = None,
                      include_backups: bool = True) -> list[str]:
    """Paths of every buy-fills file of the portfolio: ``fills_<key>.json`` first, then
    ``fills_<key>[._-]*.json`` and ``fills_<key>*.bak*`` (oldest name first).
    ``include_backups=False`` leaves the ``.bak`` files out."""
    key = portfolio_key(portfolio_meta)
    if key is None:
        return []
    directory = executions_dir() if directory is None else directory
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    head = f"fills_{key}"
    main, others = [], []
    for name in names:
        if not name.startswith(head):
            continue
        rest = name[len(head):]
        if rest == ".json":
            bucket = main
        elif rest and rest[0] in _FILL_SEPARATORS and (
                rest.endswith(".json") or (include_backups and ".bak" in rest)):
            bucket = others
        else:
            continue
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            bucket.append(path)
    return main + others


def load_portfolio_fill_docs(portfolio_meta, directory: str | None = None,
                             include_backups: bool = True) -> list[dict]:
    """Every readable buy-fills document of this portfolio (see ``_fills_candidates``).
    Never raises; unreadable files are warned about and skipped."""
    docs = []
    for path in _fills_candidates(portfolio_meta, directory, include_backups):
        doc = _read_fills(path)
        if doc is not None:
            docs.append(doc)
    return docs


def _fill_key(fill: dict, default_side: str = "BUY"):
    """Identity of a fill: ``(ticker, side, deal_id, fill_ts)`` with a ``deal_id``,
    otherwise every economic field (so two files holding the same fill agree)."""
    ticker = str(fill.get("ticker") or "").strip()
    side = _fill_side(fill, default_side)
    deal_id = fill.get("deal_id")
    if deal_id:
        return (ticker, side, str(deal_id), str(fill.get("fill_ts") or ""))
    return (ticker, side, None, str(fill.get("fill_ts") or ""),
            _as_float(fill.get("filled_qty")), _as_float(fill.get("filled_weight")),
            _as_float(fill.get("price")), str(fill.get("signal_run_ts") or ""))


def _stamped_fills(doc) -> list[dict]:
    """Fills of a buy document, each with the ``signal_run_ts`` of its tranche."""
    signal_run_ts = (doc or {}).get("signal_run_ts")
    out = []
    for fill in (doc or {}).get("fills") or []:
        if not isinstance(fill, dict):
            continue
        fill = dict(fill)
        if signal_run_ts and not fill.get("signal_run_ts"):
            fill["signal_run_ts"] = signal_run_ts
        out.append(fill)
    return out


def accumulate_fills(existing, new) -> dict:
    """Merge a new tranche document into the cumulative buy-fills document.

    ``existing`` is the current file (or None), ``new`` the tranche just executed.
    Top-level fields come from ``new``; ``fills`` is every fill of both, deduplicated
    by ``_fill_key`` (a fill that the new document repeats from the file is not
    added again), each stamped with its own ``signal_run_ts``; ``tranches`` lists the
    tranches seen, oldest first. Neither argument is modified.
    """
    new = dict(new or {})
    fills, seen = [], set()
    for fill in _stamped_fills(existing) + _stamped_fills(new):
        key = _fill_key(fill)
        if key in seen:
            continue
        seen.add(key)
        fills.append(fill)
    tranches = []
    for doc in (existing, new):
        for tranche in (doc or {}).get("tranches") or []:
            if isinstance(tranche, dict) and tranche not in tranches:
                tranches.append(tranche)
        if doc and doc.get("signal_run_ts"):
            tranche = {"signal_run_ts": doc["signal_run_ts"], "executed_ts": doc.get("executed_ts")}
            if not any(t.get("signal_run_ts") == tranche["signal_run_ts"] for t in tranches):
                tranches.append(tranche)
    merged = dict(existing or {})
    merged.update(new)
    merged["schema_version"] = SCHEMA_VERSION
    merged["fills"] = fills
    merged["tranches"] = tranches
    return merged


def write_portfolio_fills(portfolio_meta, payload, directory: str | None = None) -> str | None:
    """Append a tranche to ``fills_<optimizer>_<stamp>.json`` (never overwrite history).

    The history comes from the existing file and from every other fills file / backup
    of the portfolio, so a file that an older writer already overwrote is rebuilt from
    its ``.bak``. Returns the path, or None (after a warning) without a portfolio key
    or when it cannot be written.
    """
    path = portfolio_fills_path(portfolio_meta, directory)
    if path is None:
        _warn("Cannot write fills: the portfolio has no optimizer / run_ts.")
        return None
    history = None
    for doc in load_portfolio_fill_docs(portfolio_meta, directory):
        history = accumulate_fills(history, doc)
    merged = accumulate_fills(history, payload)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        _atomic_write(path, json.dumps(to_jsonable(merged), indent=2, ensure_ascii=False,
                                       allow_nan=False) + "\n")
    except Exception as exc:
        _warn(f"Could not write fills file ({path}): {exc}.")
        return None
    return path


_SELL_FILLS_PREFIX = "sell_fills_"
_SALE_STAMP = re.compile(r"\d{8}T\d{6}")
_QTY_EPS = 1e-9


def _sell_fills_candidates(portfolio_meta, directory: str | None = None) -> list[str]:
    """Paths of ``sell_fills_<optimizer>_<stamp>.json`` files that may belong to the portfolio."""
    meta = portfolio_meta or {}
    optimizer = _file_token(meta.get("portfolio_optimizer") or "")
    if not optimizer or portfolio_key(meta) is None:
        return []
    directory = executions_dir() if directory is None else directory
    try:
        names = sorted(os.listdir(directory))
    except OSError:
        return []
    head = f"{_SELL_FILLS_PREFIX}{optimizer}_"
    stamp = run_ts_stamp(meta.get("portfolio_run_ts"))
    paths = []
    for name in names:
        if not (name.startswith(head) and name.endswith(".json")):
            continue
        tail = name[len(head):-len(".json")]
        # A longer optimizer name sharing this prefix ("x" vs "x_y") ends in a
        # different tail: it must look like a stamp (or be the portfolio's own).
        if _SALE_STAMP.fullmatch(tail) or tail == stamp:
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                paths.append(path)
    return paths


def _read_sell_fills(path: str, portfolio_meta):
    """A sell-fills document if it is valid and belongs to the portfolio, else None."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"Could not read sell fills file ({path}): {exc}.")
        return None
    if not isinstance(payload, dict) or payload.get("schema_version") != SCHEMA_VERSION:
        _warn(f"Unsupported sell fills file ({path}).")
        return None
    if not isinstance(payload.get("fills", []), list):
        _warn(f"Sell fills file fills field is not a list ({path}).")
        return None
    meta = portfolio_meta or {}
    optimizer = payload.get("portfolio_optimizer")
    if optimizer and _file_token(optimizer) != _file_token(meta.get("portfolio_optimizer") or ""):
        return None
    wanted = run_ts_stamp(meta.get("portfolio_run_ts"))
    if payload.get("portfolio_run_ts"):
        owned = run_ts_stamp(payload["portfolio_run_ts"]) == wanted
    else:
        name = os.path.basename(path)
        owned = name.endswith(f"_{wanted}.json")
    if not owned:
        return None
    loaded = dict(payload)
    loaded["fills"] = payload.get("fills") or []
    return loaded


def load_portfolio_sell_fills(portfolio_meta, directory: str | None = None) -> list[dict]:
    """Every sell-fills document of this portfolio (oldest name first). Never raises."""
    docs = []
    for path in _sell_fills_candidates(portfolio_meta, directory):
        doc = _read_sell_fills(path, portfolio_meta)
        if doc is not None:
            docs.append(doc)
    return docs


def _fill_side(fill: dict, default: str) -> str:
    """BUY or SELL for a fill: explicit ``action`` / ``side``, else a negative
    ``filled_qty`` means a sale, else ``default`` (the kind of file it came from)."""
    for key in ("action", "side"):
        value = str(fill.get(key) or "").strip().upper()
        if value in ("BUY", "SELL"):
            return value
    qty = _as_float(fill.get("filled_qty"))
    if qty is not None and qty < 0:
        return "SELL"
    return default


def summarize_holdings(buy_doc, sell_docs=(), capital=None) -> dict:
    """Net position per ticker from buy-fills document(s) and sell-fills documents.

    ``buy_doc`` is one document or a list of them (every tranche file of the
    portfolio). Returns ``{ticker: {"bought_qty", "sold_qty", "net_qty",
    "bought_weight", "sold_weight", "net_weight"}}``. Quantities and weights are
    absolute values (a sale may be written as a negative ``filled_qty``); ``net_*``
    is bought - sold, floored at 0. Only fills with status filled / partial /
    partially_filled count. A fill repeated in several files (see ``_fill_key``)
    counts once. A fill with no ``filled_weight`` gets ``filled_qty * price /
    capital`` when ``capital`` (portfolio value) is given. Each row also carries
    ``last_price`` (price of its latest fill, by ``fill_ts``) and ``last_fill_ts``
    when some fill has a price.
    """
    holdings: dict = {}
    first_seen: dict = {}
    last_stamp: dict = {}
    buys = buy_doc if isinstance(buy_doc, (list, tuple)) else [buy_doc]
    sources = [("BUY", _stamped_fills(doc)) for doc in buys]
    sources += [("SELL", [f for f in (doc or {}).get("fills") or []]) for doc in sell_docs or ()]
    for index, (default, fills) in enumerate(sources):
        for fill in fills:
            if not isinstance(fill, dict):
                continue
            if str(fill.get("status") or "").strip().lower() not in _APPLIED_FILL_STATUSES:
                continue
            ticker = str(fill.get("ticker") or "").strip()
            if not ticker:
                continue
            side = _fill_side(fill, default)
            qty, weight = _as_float(fill.get("filled_qty")), _as_float(fill.get("filled_weight"))
            if weight is None and capital and qty is not None:
                price = _as_float(fill.get("price"))
                if price is not None and price > 0:
                    weight = abs(qty) * price / capital
            key = _fill_key(fill, default)
            # With a deal_id a repeated fill counts once anywhere; without one only a
            # copy in ANOTHER document does (two equal fills of one file are two fills).
            if key in first_seen and (fill.get("deal_id") or first_seen[key] != index):
                continue
            first_seen.setdefault(key, index)
            row = holdings.setdefault(ticker, dict.fromkeys(
                ("bought_qty", "sold_qty", "bought_weight", "sold_weight"), 0.0))
            price = _as_float(fill.get("price"))
            if price is not None and price > 0:
                moment = _parse_iso(fill.get("fill_ts"))
                stamp = moment.timestamp() if moment is not None else float("-inf")
                if stamp >= last_stamp.get(ticker, float("-inf")):
                    last_stamp[ticker] = stamp
                    row["last_price"] = price
                    row["last_fill_ts"] = fill.get("fill_ts") if moment is not None else None
            prefix = "bought" if side == "BUY" else "sold"
            if qty is not None:
                row[f"{prefix}_qty"] += abs(qty)
            if weight is not None:
                row[f"{prefix}_weight"] += abs(weight)
    for row in holdings.values():
        row["net_qty"] = max(0.0, row["bought_qty"] - row["sold_qty"])
        row["net_weight"] = max(0.0, row["bought_weight"] - row["sold_weight"])
    return holdings


def portfolio_capital(env=None) -> float | None:
    """Portfolio value from ``PORTFOLIO_CAPITAL`` (optional), used to turn a fill's
    ``qty * price`` into a weight when the fill has no ``filled_weight``."""
    env = os.environ if env is None else env
    return _positive_number(_as_float_text(env.get("PORTFOLIO_CAPITAL")))


def _as_float_text(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def load_portfolio_holdings(portfolio_meta, directory: str | None = None,
                            include_backups: bool = True) -> dict:
    """NET held quantity per ticker from the buy and sell fills of this portfolio.

    Buy fills are the SUM of every tranche: all ``fills_<optimizer>_<stamp>*``
    files of the portfolio (``load_portfolio_fill_docs``), or the legacy lookup
    (``load_fills``) when the portfolio has no optimizer / run_ts. Sell fills come
    from ``load_portfolio_sell_fills``. See ``summarize_holdings`` for the result;
    ``{}`` when there are no fills. Never raises.
    """
    if portfolio_key(portfolio_meta) is None:
        buys = load_fills("entry_signal_tool", directory)
    else:
        buys = load_portfolio_fill_docs(portfolio_meta, directory, include_backups)
    return summarize_holdings(buys, load_portfolio_sell_fills(portfolio_meta, directory),
                              capital=portfolio_capital())


def fully_sold_tickers(holdings, rotation_state=None) -> list[str]:
    """Tickers bought and then sold down to nothing (net quantity 0), ascending.

    A ticker with sales but no recorded purchase is not listed: its position
    came from outside these fills, so a net of 0 would be a guess. A ticker that
    ``drawdown_rotation`` picked again after the sale (see ``rotation_reentered``)
    is not listed either: it is meant to be bought again.
    """
    out = []
    for ticker, row in (holdings or {}).items():
        if row.get("sold_qty", 0.0) > _QTY_EPS and row.get("bought_qty", 0.0) > _QTY_EPS \
                and row.get("net_qty", 0.0) <= _QTY_EPS \
                and not rotation_reentered(rotation_state, ticker):
            out.append(ticker)
    return sorted(out)


def rotation_reentered(rotation_state, ticker: str) -> bool:
    """True when the rotation bought ``ticker`` on a date after its last trigger.

    ``triggers[ticker]["date"]`` is the last drop that hit it; each ``history``
    entry lists the names the rotation ``bought`` that day (ISO dates compare as
    strings). A name that never triggered and was only bought is a plain new
    entry, which is also True.
    """
    state = rotation_state or {}
    trigger = (state.get("triggers") or {}).get(ticker)
    last_exit = str(trigger.get("date") or "") if isinstance(trigger, dict) else ""
    for entry in state.get("history") or []:
        if isinstance(entry, dict) and ticker in (entry.get("bought") or []) \
                and str(entry.get("date") or "") > last_exit:
            return True
    return False


# ------------------------------------------------------------------------------
# Current holdings: what the portfolio really holds today (weights for gex / vix)
# ------------------------------------------------------------------------------
NY = ZoneInfo("America/New_York")
_default_executions_dir = executions_dir
HOLDINGS_SNAPSHOT_SCHEMA = 1
SNAPSHOT_MAX_SESSIONS = 1
WEIGHTS_FROM_SNAPSHOT = "snapshot"
WEIGHTS_FROM_FILLS = "fills"
WEIGHTS_FROM_PORTFOLIO_FILE = "portfolio_file"


def _parse_iso(value) -> datetime | None:
    """Timezone-aware datetime from an ISO-8601 string, or None (also when naive)."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        moment = datetime.fromisoformat(re.sub(r"Z$", "+00:00", value.strip()))
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else None


def holdings_snapshot_path(portfolio_meta, directory: str | None = None) -> str | None:
    """``<EXECUTIONS_DIR>/holdings_<optimizer>_<run_ts stamp>.json``, or None."""
    key = portfolio_key(portfolio_meta)
    if key is None:
        return None
    directory = executions_dir() if directory is None else directory
    return os.path.join(directory, f"holdings_{key}.json")


def _positive_float(value) -> float | None:
    number = _as_float(value)
    return number if number is not None and number > 0 else None


def _snapshot_fresh(as_of: datetime, today: date, sessions_fn=None) -> tuple[bool, str]:
    """(usable, reason). Fresh = at most ``SNAPSHOT_MAX_SESSIONS`` NYSE sessions
    between the snapshot's New York date (exclusive) and ``today`` (inclusive)."""
    as_of_day = as_of.astimezone(NY).date()
    if as_of_day > today + timedelta(days=1):
        return False, f"as_of {as_of.isoformat()} is in the future"
    if as_of_day >= today:
        return True, ""
    sessions = (sessions_fn or nyse_sessions_between)(as_of_day + timedelta(days=1), today)
    if len(sessions) > SNAPSHOT_MAX_SESSIONS:
        return False, (f"as_of {as_of.isoformat()} is {len(sessions)} NYSE sessions old "
                       f"(max {SNAPSHOT_MAX_SESSIONS})")
    return True, ""


def _snapshot_positions(path: str, portfolio_meta, today: date, sessions_fn, notes: list):
    """``({ticker: {qty, price, market_value}}, as_of_text)`` from a fresh, valid
    snapshot, or None (after a warning in ``notes``) when it is missing or unusable."""
    def reject(reason):
        notes.append(f"holdings snapshot ignored ({path}): {reason}.")
        return None

    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return reject(f"unreadable ({exc})")
    if not isinstance(payload, dict) or payload.get("schema_version") != HOLDINGS_SNAPSHOT_SCHEMA:
        return reject("not a schema_version 1 object")
    meta = portfolio_meta or {}
    optimizer = payload.get("portfolio_optimizer")
    if optimizer and _file_token(optimizer) != _file_token(meta.get("portfolio_optimizer") or ""):
        return reject("belongs to another optimizer")
    if payload.get("portfolio_run_ts") and \
            run_ts_stamp(payload["portfolio_run_ts"]) != run_ts_stamp(meta.get("portfolio_run_ts")):
        return reject("belongs to another portfolio run")
    as_of = _parse_iso(payload.get("as_of"))
    if as_of is None:
        return reject("as_of missing or not ISO-8601 with a UTC offset")
    fresh, why = _snapshot_fresh(as_of, today, sessions_fn)
    if not fresh:
        return reject(why)
    rows = payload.get("positions")
    if not isinstance(rows, list):
        return reject("positions is not a list")
    positions: dict = {}
    for row in rows:
        ticker = str((row or {}).get("ticker") or "").strip() if isinstance(row, dict) else ""
        qty = _as_float(row.get("qty")) if ticker else None
        if qty is None:
            continue
        if qty < -_QTY_EPS:
            notes.append(f"snapshot: {ticker} has negative qty {qty:g}; dropped.")
        if qty <= _QTY_EPS:
            continue
        price = _positive_float(row.get("price"))
        value = _positive_float(row.get("market_value"))
        if value is None and price is not None:
            value = qty * price
        if value is None:
            notes.append(f"snapshot: {ticker} has no price or market_value; dropped.")
            continue
        slot = positions.setdefault(ticker, {"qty": 0.0, "price": price, "market_value": 0.0,
                                             "price_source": "snapshot"})
        slot["qty"] += qty
        slot["market_value"] += value
        slot["price"] = value / slot["qty"]
    if not positions:
        return reject("no valid positions")
    return positions, str(payload["as_of"])


def _fills_positions(portfolio_meta, directory, include_backups, prices, price_fn, notes: list):
    """``(positions, as_of, price_fallback)`` from the net fills, or None when there are
    no fills or none can be valued. Net = buys - sells (``load_portfolio_holdings``)."""
    holdings = load_portfolio_holdings(portfolio_meta, directory, include_backups)
    if not holdings:
        return None
    positions, fallback, latest = {}, [], None
    for ticker, row in sorted(holdings.items()):
        net = row["bought_qty"] - row["sold_qty"]
        if net < -_QTY_EPS:
            notes.append(f"fills: {ticker} sold more than bought (net {net:g}); dropped.")
        if net <= _QTY_EPS:
            continue
        price, source = _positive_float((prices or {}).get(ticker)), "prices"
        if price is None and price_fn is not None:
            try:
                price, source = _positive_float(price_fn(ticker)), "price_fn"
            except Exception as exc:
                notes.append(f"fills: price for {ticker} unavailable ({exc}).")
        if price is None:
            price, source = _positive_float(row.get("last_price")), "last_fill"
        if price is None:
            notes.append(f"fills: {ticker} has no price; dropped.")
            continue
        if source == "last_fill":
            fallback.append(ticker)
        positions[ticker] = {"qty": net, "price": price, "market_value": net * price,
                             "price_source": source}
        moment = _parse_iso(row.get("last_fill_ts"))
        if moment is not None and (latest is None or moment > latest[0]):
            latest = (moment, row["last_fill_ts"])
    if not positions:
        return None
    if fallback:
        notes.append("fills: valued at the last fill price (no current price): "
                     + ", ".join(fallback) + ".")
    return positions, (latest[1] if latest else None), fallback


def _weights_from_values(positions: dict) -> dict:
    total = sum(p["market_value"] for p in positions.values())
    return {t: p["market_value"] / total for t, p in sorted(positions.items())}


def current_holdings(portfolio, executions_dir: str | None = None, *, prices=None,
                     price_fn=None, today: date | None = None, sessions_fn=None,
                     include_backups: bool = True) -> dict:
    """What the portfolio really holds now, with weights over the invested positions.

    ``portfolio`` is the dict of ``load_portfolio`` (``weights`` and ``portfolio_optimizer`` /
    ``portfolio_run_ts``). Sources, in priority order:

    1. ``holdings_<key>.json`` (``HOLDINGS_SNAPSHOT_SCHEMA``, written by the executor from the
       broker's positions), only when its ``as_of`` is at most ``SNAPSHOT_MAX_SESSIONS`` NYSE
       sessions old; otherwise it is ignored with a warning.
    2. Net fills: buy fills minus sell fills (``load_portfolio_holdings``), valued at
       ``prices[ticker]``, else ``price_fn(ticker)``, else the ticker's last fill price (listed
       in ``price_fallback_tickers``). ``include_backups=False`` ignores ``fills_*.bak*``.
    3. The portfolio file's own weights.

    Quantities <= 0 are dropped (a net sale beyond the purchases warns). Weights are
    market value / total market value of the invested positions (sum 1; cash is not part of
    it). Never raises; the executions folder is only read.

    Returns ``{"holdings": {ticker: {"qty", "price", "market_value", "weight", ...}},
    "weights": {ticker: weight}, "weights_source": "snapshot" | "fills" | "portfolio_file",
    "as_of": ISO text or None, "price_fallback_tickers": [...], "warnings": [...]}``.
    """
    notes: list = []
    directory = executions_dir if executions_dir is not None else _default_executions_dir()
    today = today or cycle_today()
    meta = portfolio or {}
    source, as_of, positions, fallback = None, None, None, []

    path = holdings_snapshot_path(meta, directory)
    if path:
        found = _snapshot_positions(path, meta, today, sessions_fn, notes)
        if found:
            positions, as_of = found
            source = WEIGHTS_FROM_SNAPSHOT
    if positions is None and portfolio_key(meta) is not None:
        found = _fills_positions(meta, directory, include_backups, prices, price_fn, notes)
        if found:
            positions, as_of, fallback = found
            source = WEIGHTS_FROM_FILLS

    if positions is not None:
        weights = _weights_from_values(positions)
        detail = {t: dict(positions[t], weight=weights[t]) for t in weights}
    else:
        source, as_of = WEIGHTS_FROM_PORTFOLIO_FILE, meta.get("portfolio_run_ts")
        weights = {str(t): float(w) for t, w in (meta.get("weights") or {}).items()}
        detail = {t: {"qty": None, "price": None, "market_value": None, "weight": w}
                  for t, w in weights.items()}
    for note in notes:
        _warn(note)
    return {"holdings": detail, "weights": weights, "weights_source": source, "as_of": as_of,
            "price_fallback_tickers": fallback, "warnings": notes}


def pipeline_dir(env=None) -> str:
    """``PIPELINE_DIR``, else the parent of the signals base (``SIGNALS_OUT_DIR``).

    Derived from the base, never from the per-portfolio subfolder."""
    env = os.environ if env is None else env
    explicit = env.get("PIPELINE_DIR")
    if explicit:
        return explicit
    return os.path.dirname(os.path.abspath(signals_base_dir(env)))


def entry_state_path(portfolio_meta, env=None) -> str:
    """Entry state of this portfolio: ``ENTRY_STATE_FILE``, else
    ``<pipeline dir>/state/entry_state_<optimizer>_<run_ts stamp>.json``."""
    env = os.environ if env is None else env
    explicit = env.get("ENTRY_STATE_FILE")
    if explicit:
        return explicit
    key = portfolio_key(portfolio_meta) or "hardcoded_fallback"
    return os.path.join(pipeline_dir(env), "state", f"entry_state_{key}.json")


# ------------------------------------------------------------------------------
# Entry phase: days 1..5 of a portfolio, in NYSE sessions
# ------------------------------------------------------------------------------
ENTRY_PHASE_DAYS = 5


def nyse_sessions_between(start: date, end: date) -> list[date]:
    """NYSE sessions in ``[start, end]``. Without a calendar library it falls back to
    Monday-Friday (holidays are then counted as sessions) and warns."""
    if end < start:
        return []
    try:
        import pandas_market_calendars as mcal
    except ImportError:
        mcal = None
    try:
        if mcal is not None:
            schedule = mcal.get_calendar("NYSE").schedule(
                start_date=start.isoformat(), end_date=end.isoformat())
            return [stamp.date() for stamp in schedule.index]
        import exchange_calendars as xcals
        calendar = xcals.get_calendar("XNYS")
        return [stamp.date() for stamp in calendar.sessions_in_range(
            pd.Timestamp(start), pd.Timestamp(end))]
    except Exception as exc:
        _warn(f"NYSE calendar unavailable ({exc}); counting Monday-Friday as sessions.")
        days = (end - start).days + 1
        return [start + timedelta(days=i) for i in range(days) if (start + timedelta(days=i)).weekday() < 5]


def _read_json_object(path: str):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _fill_date(fill_or_doc):
    for key in ("fill_ts", "executed_ts"):
        parsed = _iso_date((fill_or_doc or {}).get(key))
        if parsed is not None:
            return parsed
    return None


def entry_start_date(portfolio_meta, today=None, env=None, directory: str | None = None) -> date:
    """Day 1 of this portfolio's entry.

    1. ``entry_start_date`` in the entry state file (written by entry_signal_tool).
    2. A state file without it but with entry activity (an older file): the earliest
       fill date of the portfolio, else the portfolio ``run_ts`` date.
    3. No state, no activity: ``today`` (the first tranche is day 1).
    """
    today = _iso_date(today) or cycle_today()
    state = _read_json_object(entry_state_path(portfolio_meta, env)) or {}
    recorded = _iso_date(state.get("entry_start_date"))
    if recorded is not None:
        return recorded
    active = any(state.get(key) for key in
                 ("ultima_actualizacion", "pending_signal_run_ts", "last_tranche_date"))
    if not active:
        return today
    dates = []
    for doc in load_portfolio_fill_docs(portfolio_meta, directory):
        dates.append(_fill_date(doc))
        dates += [_fill_date(f) for f in doc.get("fills") or [] if isinstance(f, dict)]
    dates = [d for d in dates if d]
    if dates:
        return min(dates)
    return portfolio_horizon_fields(portfolio_meta)["run_date"] or today


def entry_phase_info(portfolio_meta, today=None, env=None, sessions_fn=None,
                     directory: str | None = None) -> dict:
    """Where ``today`` falls in the entry phase of the portfolio.

    ``day`` is the number of NYSE sessions in ``[start_date, today]`` (at least 1);
    ``active`` is true on days 1..``ENTRY_PHASE_DAYS``. ``sessions_fn(start, end)``
    replaces the calendar (tests, run_cycle).
    """
    today = _iso_date(today) or cycle_today()
    start = entry_start_date(portfolio_meta, today, env, directory)
    sessions = (sessions_fn or nyse_sessions_between)(start, today)
    day = max(1, len(sessions))
    return {"day": day, "start_date": start.isoformat(), "active": day <= ENTRY_PHASE_DAYS,
            "last_day": ENTRY_PHASE_DAYS}


def session_day(start, day, sessions_fn=None) -> int:
    """Entry-phase day number of calendar date ``day`` for an entry that began on ``start``."""
    start, day = _iso_date(start), _iso_date(day)
    return max(1, len((sessions_fn or nyse_sessions_between)(start, day)))


def load_pause_mark(portfolio_meta, today=None) -> dict:
    """The pause mark that ``drawdown_rotation`` wrote for ``today``.

    Reads ``<signals dir>/drawdown_rotation.json`` (``data.pause``, see
    drawdown_rotation). Returns ``{"tickers": [...], "returns": {...}, "entry_day": n}``
    only for a mark of this portfolio, dated ``today``, in mode ``pause``; otherwise
    ``{"tickers": []}``. Never raises.
    """
    today = _iso_date(today) or cycle_today()
    path = os.path.join(resolve_signals_dir(portfolio_meta), "drawdown_rotation.json")
    payload = _read_json_object(path) if os.path.isfile(path) else None
    empty = {"tickers": [], "returns": {}, "entry_day": None}
    if not payload:
        return empty
    meta = portfolio_meta or {}
    if payload.get("portfolio_run_ts") != meta.get("portfolio_run_ts"):
        return empty
    pause = (payload.get("data") or {}).get("pause")
    if not isinstance(pause, dict) or pause.get("mode") != "pause":
        return empty
    if _iso_date(pause.get("cycle_date")) != today:
        return empty
    tickers = sorted({str(t) for t in pause.get("tickers") or [] if t})
    returns = pause.get("returns") if isinstance(pause.get("returns"), dict) else {}
    return {"tickers": tickers, "returns": returns, "entry_day": pause.get("entry_day")}


def load_active_management_targets(portfolio_meta, start_date, sessions_fn=None) -> tuple[dict, dict]:
    """Current targets from the latest ``active_management`` output, if it counts.

    Returns ``(targets, info)``. ``targets`` is ``{ticker: target_weight}`` (CASH
    excluded) and is empty unless the output belongs to this portfolio AND
    ``active_management`` ran AFTER the entry phase (its run date is on entry day 6
    or later: during days 1..5 it must not run, and an older output does not
    describe a later entry). ``info`` has ``status`` ("used", "missing",
    "in_entry_phase", "other_portfolio") plus ``run_ts`` and ``entry_day``.
    """
    path = os.path.join(resolve_signals_dir(portfolio_meta), "active_management.json")
    payload = _read_json_object(path) if os.path.isfile(path) else None
    if not payload:
        return {}, {"status": "missing"}
    meta = portfolio_meta or {}
    if payload.get("portfolio_run_ts") != meta.get("portfolio_run_ts"):
        return {}, {"status": "other_portfolio"}
    ran = _iso_date(str(payload.get("run_ts") or "")[:10])
    if ran is None:
        return {}, {"status": "missing"}
    day = session_day(start_date, ran, sessions_fn)
    info = {"status": "used", "run_ts": payload.get("run_ts"), "entry_day": day}
    if day <= ENTRY_PHASE_DAYS:
        info["status"] = "in_entry_phase"
        return {}, info
    targets = {}
    for row in (payload.get("data") or {}).get("rebalances") or []:
        if not isinstance(row, dict) or str(row.get("ticker")) == "CASH":
            continue
        weight = _as_float(row.get("target_weight"))
        if weight is not None and weight >= 0:
            targets[str(row["ticker"])] = weight
    return targets, info


# ------------------------------------------------------------------------------
# Rotation state (drawdown_rotation.py -> entry_signal_tool.py)
# ------------------------------------------------------------------------------
ROTATION_STATE_VERSION = 1


def rotation_state_path(portfolio_meta, env=None) -> str:
    """Rotation state of this portfolio: ``ROTATION_STATE_FILE``, else
    ``<pipeline dir>/state/rotation_state_<optimizer>_<run_ts stamp>.json``.

    One file per portfolio, like the entry state: a new optimized portfolio
    starts with no rotations, because its weights already supersede them."""
    env = os.environ if env is None else env
    explicit = env.get("ROTATION_STATE_FILE")
    if explicit:
        return explicit
    key = portfolio_key(portfolio_meta) or "hardcoded_fallback"
    return os.path.join(pipeline_dir(env), "state", f"rotation_state_{key}.json")


def empty_rotation_state(portfolio_meta=None) -> dict:
    meta = portfolio_meta or {}
    return {
        "schema_version": ROTATION_STATE_VERSION,
        "portfolio": {
            "optimizer": meta.get("portfolio_optimizer"),
            "run_ts": meta.get("portfolio_run_ts"),
        },
        "target_overrides": {},
        "triggers": {},
        "history": [],
    }


def load_rotation_state(portfolio_meta, path: str | None = None, env=None) -> dict:
    """Read the rotation state, or an empty one. Never raises."""
    path = path or rotation_state_path(portfolio_meta, env)
    if not os.path.isfile(path):
        return empty_rotation_state(portfolio_meta)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"Could not read rotation state ({path}): {exc}. Starting empty.")
        return empty_rotation_state(portfolio_meta)
    if not isinstance(payload, dict) or payload.get("schema_version") != ROTATION_STATE_VERSION:
        _warn(f"Unsupported rotation state ({path}). Starting empty.")
        return empty_rotation_state(portfolio_meta)
    state = empty_rotation_state(portfolio_meta)
    for key in ("target_overrides", "triggers"):
        if isinstance(payload.get(key), dict):
            state[key] = payload[key]
    if isinstance(payload.get("history"), list):
        state["history"] = payload["history"]
    return state


def save_rotation_state(state: dict, portfolio_meta, path: str | None = None) -> str | None:
    """Atomic write of the rotation state. Returns the path, or None after a warning."""
    path = path or rotation_state_path(portfolio_meta)
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        text = json.dumps(to_jsonable(state), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        _atomic_write(path, text)
        return path
    except Exception as exc:
        _warn(f"Could not write rotation state ({path}): {exc}.")
        return None


def parse_ticker_list(raw) -> list[str]:
    """Tickers from a comma/whitespace separated string, in order, without blanks or
    duplicates. ``None`` or blank gives ``[]``."""
    return list(dict.fromkeys(part for part in re.split(r"[,\s]+", str(raw or "")) if part))


def apply_rotation_overrides(weights: dict, state) -> tuple[dict, list[str]]:
    """Target weights after the rotations recorded for this portfolio.

    ``state["target_overrides"]`` maps ticker -> new target weight: a trimmed
    holding gets its reduced weight, a liquidated one 0 (it leaves the dict),
    a new name from the rotation its share of the freed weight. Returns
    ``(weights, notes)``; ``weights`` is unchanged when there are no overrides.
    """
    overrides = (state or {}).get("target_overrides") or {}
    if not overrides:
        return dict(weights), []
    out = dict(weights)
    notes = []
    for ticker, value in overrides.items():
        number = _as_float(value)
        if number is None or number < 0:
            continue
        ticker = str(ticker)
        before = out.get(ticker)
        if number <= _ZERO_WEIGHT:
            if ticker in out:
                del out[ticker]
                notes.append(f"{ticker}: liquidated by drawdown_rotation")
            continue
        out[ticker] = number
        if before is None:
            notes.append(f"{ticker}: new target {number:.4f} from drawdown_rotation")
        elif abs(before - number) > 1e-9:
            notes.append(f"{ticker}: target {before:.4f} -> {number:.4f} by drawdown_rotation")
    return out, notes


# ------------------------------------------------------------------------------
# Manual overrides (ARES -> entry_signal_tool, drawdown_rotation, active_management)
# ------------------------------------------------------------------------------
MANUAL_OVERRIDES_VERSION = 1
MANUAL_OVERRIDES_ENV = "MANUAL_OVERRIDES_FILE"
STRICT_GATE_ENV = "MANUAL_OVERRIDES_STRICT_GATE"
OVERRIDE_ACTIONS = ("replace", "reject", "add", "remove")
REQUIRES_VERIFICATION = "REQUIRES_VERIFICATION"
GATE_BUY = "BUY"
GATE_BLOCKED = "BLOCKED"
_REPLACED_REQUIRED = ("replace", "reject", "remove")
_CHOSEN_REQUIRED = ("replace", "add")


def manual_overrides_path(env=None) -> str:
    """``MANUAL_OVERRIDES_FILE``, else ``<pipeline dir>/state/manual_overrides.json``.

    One file for every portfolio: the document is keyed by ``portfolio_key``."""
    env = os.environ if env is None else env
    explicit = env.get(MANUAL_OVERRIDES_ENV)
    if explicit:
        return explicit
    return os.path.join(pipeline_dir(env), "state", "manual_overrides.json")


def strict_gate_enabled(env=None) -> bool:
    """``MANUAL_OVERRIDES_STRICT_GATE`` truthy: names that only the rotation state brings in
    (never bought, not in the portfolio file) also need verification."""
    env = os.environ if env is None else env
    return str(env.get(STRICT_GATE_ENV) or "").strip().lower() in ("1", "true", "yes", "on")


def _canon_ticker(value) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip().upper()
    return text or None


def _iso_with_offset(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(re.sub(r"Z$", "+00:00", value.strip()))
    except ValueError:
        return None
    return moment if moment.tzinfo is not None else None


def _check_override_entry(entry, where: str):
    """``(errors, normalized)`` for one override. ``normalized`` is None with any error."""
    if not isinstance(entry, dict):
        return [f"{where}: must be an object"], None
    errors: list[str] = []
    label = f"{where} (id {entry['id']!r})" if isinstance(entry.get("id"), str) and entry["id"].strip() else where

    ident = entry.get("id")
    if not isinstance(ident, str) or not ident.strip():
        errors.append(f"{label}: 'id' must be a non-empty string")
    if _iso_with_offset(entry.get("ts")) is None:
        errors.append(f"{label}: 'ts' must be an ISO-8601 timestamp with a UTC offset, got {entry.get('ts')!r}")
    action = entry.get("action")
    if action not in OVERRIDE_ACTIONS:
        errors.append(f"{label}: 'action' must be one of {', '.join(OVERRIDE_ACTIONS)}, got {action!r}")
    approved = entry.get("approved_by")
    if not isinstance(approved, str) or not approved.strip():
        errors.append(f"{label}: 'approved_by' must be a non-empty string")

    replaced_raw, chosen_raw = entry.get("replaced_ticker"), entry.get("chosen_ticker")
    replaced, chosen = _canon_ticker(replaced_raw), _canon_ticker(chosen_raw)
    if action in _REPLACED_REQUIRED and replaced is None:
        errors.append(f"{label}: 'replaced_ticker' must be a ticker for action {action!r}")
    if action == "add" and replaced_raw is not None:
        errors.append(f"{label}: 'replaced_ticker' must be null for action 'add'")
    if action in _CHOSEN_REQUIRED and chosen is None:
        errors.append(f"{label}: 'chosen_ticker' must be a ticker for action {action!r}")
    if action in ("reject", "remove") and chosen_raw is not None:
        errors.append(f"{label}: 'chosen_ticker' must be null for action {action!r}")
    if action == "replace" and replaced is not None and replaced == chosen:
        errors.append(f"{label}: 'chosen_ticker' must differ from 'replaced_ticker'")

    weight_raw = entry.get("target_weight")
    weight = _as_float(weight_raw)
    if action in _CHOSEN_REQUIRED:
        if weight is None or not 0 < weight <= 1:
            errors.append(f"{label}: 'target_weight' must be a number in (0, 1] for action {action!r}, "
                          f"got {weight_raw!r}")
    elif action in ("reject", "remove") and weight_raw is not None and weight != 0:
        errors.append(f"{label}: 'target_weight' must be null for action {action!r}")

    fills = entry.get("fills")
    if fills is not None and not (isinstance(fills, list) and all(isinstance(f, str) for f in fills)):
        errors.append(f"{label}: 'fills' must be a list of deal id strings or null")
    for field in ("source_script", "note"):
        if entry.get(field) is not None and not isinstance(entry.get(field), str):
            errors.append(f"{label}: {field!r} must be a string or null")
    if errors:
        return errors, None
    return [], {
        "id": ident.strip(), "ts": entry["ts"], "action": action,
        "replaced_ticker": replaced, "chosen_ticker": chosen,
        "target_weight": weight if action in _CHOSEN_REQUIRED else None,
        "source_script": entry.get("source_script"), "approved_by": approved.strip(),
        "fills": list(fills or []), "note": entry.get("note"),
    }


def _scan_manual_overrides(doc) -> dict:
    """Validate a whole document. ``errors`` are document-level and fatal (nothing in the
    file can be trusted); ``warnings`` do not change what is applied; ``portfolios`` maps
    each key to ``{fatal, errors, entries, named, account_id}`` (``named``: tickers written
    in entries that failed validation, so their meaning is unknown)."""
    out = {"errors": [], "warnings": [], "portfolios": {}}
    if not isinstance(doc, dict):
        out["errors"].append("top level must be a JSON object")
        return out
    if doc.get("schema_version") != MANUAL_OVERRIDES_VERSION:
        out["errors"].append(
            f"'schema_version' must be {MANUAL_OVERRIDES_VERSION}, got {doc.get('schema_version')!r}")
        return out
    if doc.get("updated_ts") is not None and _iso_with_offset(doc.get("updated_ts")) is None:
        out["warnings"].append(
            f"'updated_ts' should be an ISO-8601 timestamp with a UTC offset, got {doc.get('updated_ts')!r}")
    portfolios = doc.get("portfolios")
    if not isinstance(portfolios, dict):
        out["errors"].append("'portfolios' must be an object keyed by <optimizer>_<run_ts stamp>")
        return out
    for key, section in portfolios.items():
        info = {"fatal": False, "errors": [], "entries": [], "named": set(), "account_id": None}
        out["portfolios"][key] = info
        prefix = f"portfolios[{key!r}]"
        if not isinstance(section, dict):
            info["fatal"] = True
            info["errors"].append(f"{prefix}: must be an object")
            continue
        account = section.get("account_id")
        if account is not None and not isinstance(account, str):
            out["warnings"].append(f"{prefix}: 'account_id' should be a string")
        else:
            info["account_id"] = account
        entries = section.get("overrides")
        if not isinstance(entries, list):
            info["fatal"] = True
            info["errors"].append(f"{prefix}: 'overrides' must be a list")
            continue
        seen = set()
        for index, raw in enumerate(entries):
            errors, normalized = _check_override_entry(raw, f"{prefix}.overrides[{index}]")
            if normalized is not None and normalized["id"] in seen:
                errors.append(f"{prefix}.overrides[{index}] (id {normalized['id']!r}): duplicate id")
                normalized = None
            if normalized is not None:
                seen.add(normalized["id"])
                normalized["_order"] = index
                info["entries"].append(normalized)
                continue
            info["errors"] += errors
            if isinstance(raw, dict):
                info["named"].update(t for t in (_canon_ticker(raw.get("replaced_ticker")),
                                                 _canon_ticker(raw.get("chosen_ticker"))) if t)
    return out


def validate_manual_overrides(doc) -> list[str]:
    """Every problem of a parsed ``manual_overrides.json``; ``[]`` means it is valid.

    Each message names the portfolio key, the position in ``overrides`` and the field."""
    scan = _scan_manual_overrides(doc)
    problems = list(scan["errors"]) + list(scan["warnings"])
    for info in scan["portfolios"].values():
        problems += info["errors"]
    return problems


def _empty_overrides(portfolio_meta, path: str, status: str = "absent") -> dict:
    return {
        "status": status, "path": path, "key": portfolio_key(portfolio_meta) or "hardcoded_fallback",
        "account_id": None, "entries": [], "blocked": {}, "chosen": {}, "unverified": {},
        "unverified_all_state": False, "errors": [], "warnings": [],
    }


def _resolve_override_entries(entries: list[dict]):
    """Replay the valid entries oldest first (file order breaks ties): the latest word on a
    ticker wins, so ``add`` after ``remove`` brings it back."""
    blocked: dict = {}
    chosen: dict = {}
    ordered = sorted(entries, key=lambda e: (_iso_with_offset(e["ts"]), e["_order"]))
    for entry in ordered:
        action, replaced, new = entry["action"], entry["replaced_ticker"], entry["chosen_ticker"]
        label = f"{action} by {entry['approved_by']} at {entry['ts']} (override {entry['id']})"
        if replaced:
            blocked[replaced] = {"id": entry["id"], "action": action, "reason": label}
            chosen.pop(replaced, None)
        if new:
            chosen[new] = {"id": entry["id"], "action": action, "target_weight": entry["target_weight"],
                           "replaced_ticker": replaced}
            blocked.pop(new, None)
    return blocked, chosen


def load_manual_overrides(portfolio_meta, path: str | None = None, env=None) -> dict:
    """Manual overrides of THIS portfolio from ``manual_overrides.json``. Never raises.

    ``status`` is ``"absent"`` (no file, or nothing for this portfolio: behaviour unchanged),
    ``"ok"`` or ``"invalid"``. Invalid input is warned about and never trusted blindly:
    entries that pass validation still apply, and every ticker named by an entry that does
    not is in ``unverified`` (the consumers emit ``REQUIRES_VERIFICATION`` for it instead of
    BUY). When the file cannot be read at all, is not JSON, has another ``schema_version`` or
    this portfolio's section is malformed, ``unverified_all_state`` is True: which tickers it
    meant is unknown, so every ticker that comes only from the rotation / entry state needs
    verification (``effective_targets`` lists them in ``unverified``).

    Result keys: ``status, path, key, account_id, entries`` (valid, normalized),
    ``blocked`` ({ticker: {id, action, reason}}: replaced / rejected / removed, never BUY),
    ``chosen`` ({ticker: {id, action, target_weight, replaced_ticker}}), ``unverified``
    ({ticker: reason}), ``unverified_all_state``, ``errors``, ``warnings``.
    """
    env = os.environ if env is None else env
    path = path or manual_overrides_path(env)
    result = _empty_overrides(portfolio_meta, path)
    if not os.path.isfile(path):
        return result

    def fail(message: str) -> dict:
        message = f"manual overrides {path}: {message}"
        _warn(f"{message}. Tickers that come only from the rotation / entry state are marked "
              f"{REQUIRES_VERIFICATION} until the file is fixed.")
        result.update(status="invalid", unverified_all_state=True)
        result["errors"].append(message)
        return result

    try:
        with open(path, "r", encoding="utf-8") as handle:
            doc = json.load(handle)
    except OSError as exc:
        return fail(f"could not be read ({exc})")
    except ValueError as exc:
        return fail(f"is not valid JSON ({exc})")
    scan = _scan_manual_overrides(doc)
    if scan["errors"]:
        return fail("; ".join(scan["errors"]))
    for message in scan["warnings"]:
        _warn(f"manual overrides {path}: {message}")
        result["warnings"].append(message)

    key = result["key"]
    for other, info in scan["portfolios"].items():
        if other != key:
            for message in info["errors"]:
                _warn(f"manual overrides {path}: {message} (another portfolio; ignored here)")
    info = scan["portfolios"].get(key)
    if info is None:
        return result
    result["account_id"] = info["account_id"]
    if info["fatal"]:
        return fail("; ".join(info["errors"]))
    result["status"] = "ok"
    result["entries"] = info["entries"]
    result["blocked"], result["chosen"] = _resolve_override_entries(info["entries"])
    if info["errors"]:
        result["status"] = "invalid"
        result["errors"] = list(info["errors"])
        for message in info["errors"]:
            _warn(f"manual overrides {path}: {message}. Its tickers are marked {REQUIRES_VERIFICATION}.")
        for ticker in sorted(info["named"]):
            result["unverified"][ticker] = (
                f"named by an invalid entry of manual_overrides.json ({path})")
        if not info["named"]:
            result["unverified_all_state"] = True
    return result


def _key_for(mapping: dict, canon: str):
    for key in mapping:
        if _canon_ticker(str(key)) == canon:
            return key
    return None


def _rotation_names(rotation_state) -> set[str]:
    out = set()
    for ticker, value in ((rotation_state or {}).get("target_overrides") or {}).items():
        number = _as_float(value)
        if number is not None and number > _ZERO_WEIGHT:
            out.add(_canon_ticker(str(ticker)) or "")
    out.discard("")
    return out


def _pending_targets(*states) -> dict:
    out: dict = {}
    for state in states:
        raw = (state or {}).get("pending_targets")
        if not isinstance(raw, dict):
            continue
        for ticker, value in raw.items():
            number = _as_float(value)
            if number is not None and number > 0:
                out[str(ticker)] = number
    return out


def effective_targets(weights: dict, rotation_state=None, entry_state=None, overrides=None) -> dict:
    """Target weights after the rotation state AND the manual overrides.

    Precedence, highest first: manual overrides (``load_manual_overrides``), the rotation
    state's ``target_overrides``, the portfolio file's ``weights``. The entry state's
    ``pending_targets`` (and the rotation state's, if it has any) are cleaned the same way:
    a replaced / rejected / removed ticker leaves them and a chosen one carries the override
    target. Without overrides the result is exactly ``apply_rotation_overrides``.

    Returns ``{"targets", "notes", "override_notes", "pending_targets", "blocked", "chosen",
    "unverified", "rotation_names"}``. ``blocked`` / ``chosen`` / ``unverified`` are keyed by
    upper-case ticker. ``unverified`` also lists, when the overrides file is unusable as a
    whole (``unverified_all_state``), every ticker present only through the rotation state or
    the pending targets.
    """
    targets, notes = apply_rotation_overrides(weights, rotation_state)
    pending = _pending_targets(rotation_state, entry_state)
    names = _rotation_names(rotation_state)
    ov = overrides or {}
    blocked, chosen = dict(ov.get("blocked") or {}), dict(ov.get("chosen") or {})
    unverified = dict(ov.get("unverified") or {})
    override_notes: list[str] = []

    for canon, info in sorted(blocked.items()):
        for book, label in ((targets, "target"), (pending, "pending target")):
            found = _key_for(book, canon)
            if found is not None:
                del book[found]
                override_notes.append(f"{found}: {label} removed by manual override ({info['reason']})")
    for canon, info in sorted(chosen.items()):
        found = _key_for(targets, canon) or canon
        before = targets.get(found)
        targets[found] = info["target_weight"]
        text = (f"{found}: target {info['target_weight']:.4f} from manual override "
                f"({info['action']}, {info['id']})")
        override_notes.append(text if before is None else f"{text}; was {before:.4f}")
        pending_key = _key_for(pending, canon)
        if pending_key is not None:
            pending[pending_key] = info["target_weight"]
    if ov.get("unverified_all_state"):
        state_only = set(names) | {_canon_ticker(t) for t in pending}
        for canon in sorted(t for t in state_only if t):
            unverified.setdefault(canon, "manual_overrides.json is invalid; the state target is unconfirmed")
    return {
        "targets": targets, "notes": notes, "override_notes": override_notes,
        "pending_targets": pending, "blocked": blocked, "chosen": chosen,
        "unverified": unverified, "rotation_names": names,
    }


def _held_names(holdings) -> set[str]:
    rows = holdings or {}
    if isinstance(rows.get("holdings"), dict):
        rows = rows["holdings"]
    return {t for t in (_canon_ticker(str(k)) for k in rows) if t}


def buy_gate(ticker, effective: dict, portfolio_weights=None, holdings=None, strict=None,
             own_picks=()) -> tuple[str, str | None]:
    """May a signal emit BUY for ``ticker``? Returns ``(status, reason)``.

    ``status`` is ``"BLOCKED"`` (replaced / rejected / removed by a manual override: never
    BUY), ``"REQUIRES_VERIFICATION"`` or ``"BUY"``. In this order:

    1. blocked by an override -> BLOCKED;
    2. unverified (named by an invalid override entry, or state-only while the file is
       unusable) -> REQUIRES_VERIFICATION;
    3. chosen by an override, in the portfolio file, or in the net holdings / fills
       (``holdings`` is ``load_portfolio_holdings`` or ``current_holdings``) -> BUY;
    4. otherwise the ticker has no known origin -> REQUIRES_VERIFICATION. Names the rotation
       brings in (``rotation_state`` ``target_overrides``) and ``own_picks`` (what the calling
       script just selected itself) are the normal rotation flow and pass, unless
       ``strict`` (default ``MANUAL_OVERRIDES_STRICT_GATE``) is on.
    """
    canon = _canon_ticker(str(ticker))
    strict = strict_gate_enabled() if strict is None else strict
    if canon in (effective.get("blocked") or {}):
        return GATE_BLOCKED, effective["blocked"][canon]["reason"]
    if canon in (effective.get("unverified") or {}):
        return REQUIRES_VERIFICATION, effective["unverified"][canon]
    if canon in (effective.get("chosen") or {}):
        return GATE_BUY, None
    if canon in {_canon_ticker(str(t)) for t in (portfolio_weights or {})} or canon in _held_names(holdings):
        return GATE_BUY, None
    if not strict and (canon in (effective.get("rotation_names") or set())
                       or canon in {_canon_ticker(str(t)) for t in own_picks}):
        return GATE_BUY, None
    return REQUIRES_VERIFICATION, (
        "not in the portfolio file, not in the net holdings / fills and not chosen in manual_overrides.json")


def apply_buy_gate(rows, effective: dict, portfolio_weights=None, holdings=None, strict=None,
                   own_picks=(), blocked_as: str = "drop") -> tuple[list, list]:
    """Run ``buy_gate`` over the BUY rows of a signal. Returns ``(rows, flagged)``.

    ``rows`` are dicts with ``ticker`` and ``action`` (entries, rebalances); rows that are
    not BUY pass untouched. A BLOCKED row is dropped (``blocked_as="drop"``) or becomes a
    HOLD at its current weight (``"hold"``, keeps one row per ticker). A REQUIRES_VERIFICATION
    row keeps its place but ``action`` and ``status`` are ``"REQUIRES_VERIFICATION"`` and
    ``verification_reason`` says why; the original action is in ``original_action``.
    ``flagged`` lists ``{"ticker", "status", "reason"}`` for every row that changed.
    """
    out, flagged = [], []
    for row in rows or []:
        if not isinstance(row, dict) or str(row.get("action") or "").upper() != "BUY":
            out.append(row)
            continue
        status, reason = buy_gate(row.get("ticker"), effective, portfolio_weights, holdings,
                                  strict, own_picks)
        if status == GATE_BUY:
            out.append(row)
            continue
        flagged.append({"ticker": row.get("ticker"), "status": status, "reason": reason})
        if status == REQUIRES_VERIFICATION:
            out.append(dict(row, action=REQUIRES_VERIFICATION, status=REQUIRES_VERIFICATION,
                            original_action="BUY", verification_reason=reason))
        elif blocked_as == "hold":
            current = row.get("current_weight")
            out.append(dict(row, action="HOLD", target_weight=current, delta_weight=0.0,
                            original_action="BUY", override_reason=reason))
    return out, flagged


def sanitize_entry_pending(estado, effective: dict):
    """Entry state whose ``pending_targets`` follow the manual overrides: a blocked ticker
    leaves, a chosen one carries the override target. The input is not modified; the same
    object comes back when nothing changes."""
    pending = (estado or {}).get("pending_targets")
    if not pending:
        return estado
    blocked, chosen = effective.get("blocked") or {}, effective.get("chosen") or {}
    cleaned, changed = {}, False
    for ticker, value in pending.items():
        canon = _canon_ticker(str(ticker))
        if canon in blocked:
            changed = True
            continue
        if canon in chosen and value != chosen[canon]["target_weight"]:
            value, changed = chosen[canon]["target_weight"], True
        cleaned[ticker] = value
    if not changed:
        return estado
    out = copy.deepcopy(estado)
    out["pending_targets"] = cleaned
    return out


def describe_overrides(overrides, effective: dict | None = None) -> dict | None:
    """Short, JSON-ready summary for a signal's ``data`` (None when there is no file / entry)."""
    ov = overrides or {}
    if ov.get("status", "absent") == "absent":
        return None
    effective = effective or {}
    return {
        "status": ov["status"], "path": ov["path"], "key": ov["key"],
        "blocked": {t: v["reason"] for t, v in sorted((effective.get("blocked") or ov["blocked"]).items())},
        "chosen": {t: v["target_weight"] for t, v in sorted((effective.get("chosen") or ov["chosen"]).items())},
        "unverified": dict(sorted((effective.get("unverified") or ov["unverified"]).items())),
        "errors": list(ov.get("errors") or []),
    }


def load_fills(script: str = "entry_signal_tool", directory: str | None = None):
    """Read a fills document or return None. Never raises."""
    path = locate_fills_file(script, directory)
    if not path:
        return None
    return _read_fills(path)


def _read_fills(path: str):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        _warn(f"Could not read fills file ({path}): {exc}.")
        return None
    if not isinstance(payload, dict):
        _warn(f"Fills file is not a JSON object ({path}).")
        return None
    if payload.get("schema_version") != SCHEMA_VERSION:
        _warn(
            f"Unsupported fills schema_version {payload.get('schema_version')!r} ({path})."
        )
        return None
    if not isinstance(payload.get("signal_run_ts"), str) or not payload["signal_run_ts"]:
        _warn(f"Fills file is missing signal_run_ts ({path}).")
        return None
    fills = payload.get("fills", [])
    if not isinstance(fills, list):
        _warn(f"Fills file fills field is not a list ({path}).")
        return None
    loaded = dict(payload)
    loaded["fills"] = fills
    return loaded


def _as_float(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    if not math.isfinite(number):
        return None
    return number


def _blank_activo():
    return {"pct_ya_invertido": 0.0, "pct_cash_consolidado": 0.0, "decision_final": None}


def apply_entry_fills(estado, payload, cycle_length: int = 5, today: str | None = None):
    """Advance entry state only when ``payload['signal_run_ts']`` matches.

    Returns ``(estado, applied)``. A match adds ``filled_weight / target_weight``
    to ``pct_ya_invertido`` for BUY fills whose status is ``filled``, ``partial``
    or ``partially_filled``. ``filled_weight`` is a portfolio weight (same units
    as ``tranche_weight``). In a cumulative file only the fills whose own
    ``signal_run_ts`` is the pending one count. Pending cash decisions on that signal are applied
    too. The input dict is left unchanged when the file does not match.
    """
    if not estado or not payload:
        return estado, False
    pending = estado.get("pending_signal_run_ts")
    if not pending or payload.get("signal_run_ts") != pending:
        return estado, False

    updated = copy.deepcopy(estado)
    activos = updated.setdefault("activos", {})
    targets = updated.get("pending_targets") or {}
    for fill in payload.get("fills") or []:
        if not isinstance(fill, dict):
            continue
        status = str(fill.get("status") or "").strip().lower()
        if status not in _APPLIED_FILL_STATUSES:
            continue
        action = str(fill.get("action") or "BUY").strip().upper()
        if action != "BUY":
            continue
        # A cumulative file also holds earlier tranches: only the fills of the
        # pending signal advance the state (fills without the field are its own).
        own = fill.get("signal_run_ts")
        if own and own != pending:
            continue
        ticker = str(fill.get("ticker") or "").strip()
        filled = _as_float(fill.get("filled_weight"))
        target = _as_float(targets.get(ticker))
        if not ticker or filled is None or filled < 0 or target is None or target <= 0:
            continue
        activo = activos.setdefault(ticker, _blank_activo())
        current = _as_float(activo.get("pct_ya_invertido")) or 0.0
        activo["pct_ya_invertido"] = min(1.0, current + filled / target)

    for ticker, cash_frac in (updated.get("pending_cash") or {}).items():
        frac = _as_float(cash_frac)
        if frac is None:
            continue
        activo = activos.setdefault(str(ticker), _blank_activo())
        activo["pct_cash_consolidado"] = min(1.0, max(0.0, frac))
        activo["decision_final"] = "CASH"

    for ticker, decision in (updated.get("pending_decisions") or {}).items():
        if decision != "ENTRAR":
            continue
        activo = activos.setdefault(str(ticker), _blank_activo())
        if activo.get("decision_final") != "CASH":
            activo["decision_final"] = "ENTRAR"

    pending_day = updated.get("pending_cycle_day")
    pending_cycle = updated.get("pending_cycle")
    same_cycle = not (isinstance(pending_cycle, int) and not isinstance(pending_cycle, bool)) \
        or pending_cycle == _as_int(updated.get("ciclo"), 1)
    if isinstance(pending_day, int) and not isinstance(pending_day, bool):
        if same_cycle:
            # A late confirmation of an older day must not pull the cycle back.
            pending_day = max(pending_day, _as_int(updated.get("dia_ciclo"), 1))
        updated["dia_ciclo"] = pending_day
        updated["ciclo_cerrado"] = pending_day >= int(cycle_length)
    if isinstance(pending_cycle, int) and not isinstance(pending_cycle, bool):
        updated["ciclo"] = pending_cycle

    executed = payload.get("executed_ts")
    if isinstance(executed, str) and len(executed) >= 10:
        updated["ultima_actualizacion"] = executed[:10]
    else:
        updated["ultima_actualizacion"] = today or datetime.now(timezone.utc).date().isoformat()

    updated["pending_signal_run_ts"] = None
    updated["pending_cycle_day"] = None
    updated["pending_cycle"] = None
    updated["pending_targets"] = {}
    updated["pending_cash"] = {}
    updated["pending_decisions"] = {}
    return updated, True


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def pending_is_empty_tranche(estado) -> bool:
    """True when the pending signal asked for no purchase (every ticker MANTENER).

    Nothing is waiting for fills in that case: no executor will ever write a fills
    file for it, so it must not hold the cycle day back.
    """
    estado = estado or {}
    pending = estado.get("pending_signal_run_ts")
    if not pending or estado.get("pending_targets"):
        return False
    tranche = estado.get("last_tranche")
    if isinstance(tranche, dict) and tranche.get("signal_run_ts") == pending and tranche.get("entries"):
        return False
    return True


def close_empty_tranche(estado, cycle_length: int = 5, today: str | None = None):
    """Close a pending signal that has no orders: the day is done without any fills.

    Same effect as ``apply_entry_fills`` with an empty fills list (day advances, a
    day-5 cash decision is recorded, pending fields are cleared). The tranche date and
    ``last_tranche`` are kept, so the same-day lock still sees it as "executed".
    """
    pending = (estado or {}).get("pending_signal_run_ts")
    if not pending:
        return estado
    tranche = estado.get("last_tranche")
    prepared = None
    if isinstance(tranche, dict) and tranche.get("signal_run_ts") == pending:
        prepared = estado.get("last_tranche_date")
    payload = {"signal_run_ts": pending, "fills": [], "executed_ts": prepared or today}
    updated, _ = apply_entry_fills(estado, payload, cycle_length=cycle_length, today=today)
    return updated


def reconcile_pending_entry(estado, payload, cycle_length: int = 5, today: str | None = None):
    """Settle the pending signal against the fills file. Returns ``(estado, status)``.

    ``status``: ``"none"`` (nothing pending), ``"applied"`` (the file confirms the
    pending signal), ``"closed_empty"`` (the pending signal had no orders, so the day
    is closed without fills) or ``"stale"`` (fills of another signal_run_ts; the state
    is left alone).

    A stale file never blocks anything: net holdings are always summed from every
    fills file (``load_portfolio_holdings``), and the entry signal reads them directly,
    so the state only has to record which cycle day was handled.
    """
    if not estado or not estado.get("pending_signal_run_ts"):
        return estado, "none"
    if payload and payload.get("signal_run_ts") == estado["pending_signal_run_ts"]:
        updated, applied = apply_entry_fills(estado, payload, cycle_length=cycle_length, today=today)
        return updated, "applied" if applied else "stale"
    if pending_is_empty_tranche(estado):
        return close_empty_tranche(estado, cycle_length=cycle_length, today=today), "closed_empty"
    return estado, "stale"


def invested_fraction_from_holdings(holdings, ticker: str, target_weight) -> float | None:
    """Fraction (0..1) of ``target_weight`` that the REAL net position covers.

    ``holdings`` is ``load_portfolio_holdings`` (cumulative buy fills minus sell
    fills, weights from ``filled_weight`` or ``qty * price / PORTFOLIO_CAPITAL``).
    Returns None when it cannot be known and the caller must keep the state's value:
    no fills at all, no valid target, or a position whose fills carry no weight and
    there is no capital. A sale recorded only in quantity scales the bought weight.
    A ticker with no fills while others have them is 0.
    """
    target = _as_float(target_weight)
    if not holdings or target is None or target <= 0:
        return None
    row = holdings.get(ticker)
    if not row:
        return 0.0
    bought_w, sold_w = row.get("bought_weight", 0.0), row.get("sold_weight", 0.0)
    bought_q, sold_q = row.get("bought_qty", 0.0), row.get("sold_qty", 0.0)
    if bought_w <= _ZERO_WEIGHT and sold_w <= _ZERO_WEIGHT:
        return 0.0 if bought_q <= _QTY_EPS and sold_q <= _QTY_EPS else None
    if bought_w <= _ZERO_WEIGHT:
        return None
    if sold_q > _QTY_EPS and sold_w <= _ZERO_WEIGHT:
        if bought_q <= _QTY_EPS:
            return None
        net_weight = bought_w * row.get("net_qty", 0.0) / bought_q
    else:
        net_weight = row.get("net_weight", 0.0)
    return max(0.0, min(1.0, net_weight / target))


def stage_pending_entry(estado, run_ts, cycle_day, cycle, targets=None, cash=None, decisions=None,
                        prepared_date=None, tranche=None):
    """Remember the signal that is waiting for fills. Does not mark invested.

    ``prepared_date`` (America/Bogota, YYYY-MM-DD) and ``tranche`` (the
    entries/waiting that were emitted) feed the same-day lock, see
    ``tranche_lock``. Both survive ``apply_entry_fills``.
    """
    updated = copy.deepcopy(estado or {})
    if prepared_date is not None:
        updated["last_tranche_date"] = str(prepared_date)
        updated["last_tranche"] = to_jsonable(dict(tranche or {}, signal_run_ts=run_ts))
    updated["pending_signal_run_ts"] = run_ts
    updated["pending_cycle_day"] = cycle_day
    updated["pending_cycle"] = cycle
    updated["pending_targets"] = {
        str(key): float(value) for key, value in (targets or {}).items() if value is not None
    }
    updated["pending_cash"] = {
        str(key): float(value) for key, value in (cash or {}).items() if value is not None
    }
    updated["pending_decisions"] = {str(key): value for key, value in (decisions or {}).items()}
    return updated


def tranche_lock(estado, today) -> dict | None:
    """The tranche already prepared on ``today``, or None when a new one may be made.

    ``today`` is a date or YYYY-MM-DD in America/Bogota. The lock covers both a
    tranche still waiting for fills (``status`` "pending") and one whose fills
    were applied ("executed"). The returned dict has ``status``,
    ``prepared_date``, ``signal_run_ts`` and ``tranche`` (the emitted
    entries/waiting, possibly empty).
    """
    estado = estado or {}
    prepared = estado.get("last_tranche_date")
    if not prepared or str(prepared) != str(today):
        return None
    tranche = estado.get("last_tranche")
    tranche = tranche if isinstance(tranche, dict) else {}
    signal_run_ts = tranche.get("signal_run_ts")
    pending = estado.get("pending_signal_run_ts")
    status = "pending" if pending and pending == signal_run_ts else "executed"
    return {
        "status": status,
        "prepared_date": str(prepared),
        "signal_run_ts": signal_run_ts,
        "tranche": tranche,
    }


def last_executed_day(estado) -> int:
    """Cycle day last executed (or closed empty) in the state; 0 when none."""
    estado = estado or {}
    if estado.get("ultima_actualizacion") is None:
        return 0
    return max(1, _as_int(estado.get("dia_ciclo") or 1, 1))


def entry_floor_day(estado, calendar_day, cycle_length: int = 5) -> int | None:
    """Earliest cycle day a new signal may use in the entry cycle, or None.

    The entry cycle (cycle 1, not closed) follows ``calendar_day``: the NYSE sessions
    since ``entry_start_date`` (``entry_phase_info``), capped at the cycle length.
    A state behind the calendar catches up; a state ahead of it (a day was forced)
    never goes back. Later cycles do not follow the calendar: None.
    """
    estado = estado or {}
    if calendar_day is None or estado.get("ciclo_cerrado") or _as_int(estado.get("ciclo") or 1, 1) != 1:
        return None
    return min(int(cycle_length), max(1, int(calendar_day), last_executed_day(estado)))


def suggest_cycle_day(estado, cycle_length: int = 5, calendar_day=None, today=None) -> int:
    """Cycle day for the next signal. Does not write the file.

    Without ``calendar_day`` it is the day after the last *executed* one (legacy).
    With it (``entry_phase.day``) the entry cycle follows the calendar, so an empty or
    unfilled day cannot hold the state back: ``max(calendar, executed)``, and one day
    further when that day was already executed today (or the state is ahead of the
    calendar), so an executed day is never run again.
    """
    estado = estado or {}
    floor = entry_floor_day(estado, calendar_day, cycle_length)
    if floor is None:
        if estado.get("ultima_actualizacion") is None or estado.get("ciclo_cerrado"):
            return 1
        return min(max(1, _as_int(estado.get("dia_ciclo") or 1, 1)) + 1, int(cycle_length))
    executed = last_executed_day(estado)
    calendar = max(1, int(calendar_day))
    done_today = bool(today) and str(estado.get("ultima_actualizacion")) == str(today)
    if executed > calendar or (executed == calendar and done_today):
        return min(executed + 1, int(cycle_length))
    return floor


def resolve_cycle_day(explicit, estado, cycle_length: int = 5, calendar_day=None, today=None):
    """Return ``(day, warning)``. Blank explicit input uses ``suggest_cycle_day``.

    In the entry cycle an explicit day (CLI / ``ENTRY_CYCLE_DAY``) behind the calendar
    or behind the last executed day is raised to it, with a warning: an earlier day is
    never run again (a leftover ``ENTRY_CYCLE_DAY`` cannot pin the cycle).
    """
    suggested = suggest_cycle_day(estado, cycle_length, calendar_day, today)
    if explicit is None or (isinstance(explicit, str) and explicit.strip() == ""):
        return suggested, None
    try:
        dia = int(explicit)
    except (TypeError, ValueError):
        return suggested, f"invalid cycle day {explicit!r}; using {suggested}"
    if not 1 <= dia <= int(cycle_length):
        return suggested, f"cycle day {dia} outside 1..{cycle_length}; using {suggested}"
    floor = entry_floor_day(estado, calendar_day, cycle_length)
    if floor is not None and dia < floor:
        return floor, (f"cycle day {dia} is behind entry day {floor} "
                       f"(NYSE sessions since entry start / last executed day); using {floor}")
    return dia, None


def signal_cycle_number(estado, day: int, cycle_length: int = 5) -> int:
    """Cycle index for this signal. A closed cycle, or an explicit earlier day, starts the next one."""
    estado = estado or {}
    try:
        ciclo = int(estado.get("ciclo") or 1)
    except (TypeError, ValueError):
        ciclo = 1
    if estado.get("ciclo_cerrado"):
        return ciclo + 1
    try:
        stored = int(estado.get("dia_ciclo") or 1)
    except (TypeError, ValueError):
        stored = 1
    if estado.get("ultima_actualizacion") and day < stored:
        return ciclo + 1
    return max(ciclo, 1)


def _percent_number(text):
    token = str(text).strip().replace("%", "")
    try:
        number = float(token)
    except ValueError:
        return None, f"invalid invested percent {text!r}"
    if not math.isfinite(number) or number < 0 or number > 100:
        return None, f"invested percent {text!r} is outside 0..100"
    return number / 100.0, None


def _flexible_fraction(value):
    token = str(value).strip().replace("%", "")
    try:
        number = float(token)
    except ValueError:
        return None, f"invalid invested value {value!r}"
    if not math.isfinite(number) or number < 0:
        return None, f"invalid invested value {value!r}"
    if str(value).strip().endswith("%") or number > 1:
        if number > 100:
            return None, f"invested value {value!r} is outside 0..100"
        return number / 100.0, None
    return number, None


def parse_invested_overrides(raw, tickers):
    """Parse ``ENTRY_INVESTED_PCT`` / ``--invested-pct``.

    Returns ``(fractions_by_ticker | None, warnings)``. None means "use the
    state file". A bare number is a percent (0–100) applied to every ticker.
    ``GLD=40,KO=0.25`` and a JSON object are per ticker: values greater than 1
    (or written with ``%``) are percents; values in ``[0, 1]`` are fractions
    of that ticker's target weight.
    """
    if raw is None:
        return None, []
    text = str(raw).strip()
    if text == "":
        return None, []
    warnings = []
    tickers = [str(ticker) for ticker in tickers]
    if text.startswith("{"):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return None, [f"invalid invested-pct JSON ({exc})"]
        if not isinstance(parsed, dict):
            return None, ["invested-pct JSON must be an object"]
        pairs = list(parsed.items())
    elif "=" in text:
        pairs = []
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if "=" not in part:
                warnings.append(f"ignored invested override {part!r}")
                continue
            key, value = part.split("=", 1)
            pairs.append((key.strip(), value.strip()))
    else:
        number, err = _percent_number(text)
        if err:
            return None, [err]
        return {ticker: number for ticker in tickers}, []

    out = {}
    known = set(tickers)
    for key, value in pairs:
        ticker = str(key).strip()
        frac, err = _flexible_fraction(value)
        if err:
            warnings.append(f"{ticker}: {err}")
            continue
        if known and ticker not in known:
            warnings.append(f"ignored invested override for unknown ticker {ticker}")
            continue
        out[ticker] = frac
    return out, warnings
