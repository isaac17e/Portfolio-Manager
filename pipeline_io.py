"""Shared portfolio input and signal output for the Portfolio-Manager scripts.

Contract: pipeline JSON v1, section 4 (signals). Section 1 describes the
portfolio file this module reads. Writes are atomic and never raise when the
output directory cannot be created or written.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

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


def _now_bogota() -> datetime:
    return datetime.now(BOGOTA).replace(microsecond=0)


def _warn(message: str) -> None:
    print(f"[pipeline_io] {message}")


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
    return {
        "weights": weights,
        "portfolio_source": path,
        "portfolio_run_ts": run_ts if isinstance(run_ts, str) and run_ts else None,
        "portfolio_optimizer": optimizer if isinstance(optimizer, str) and optimizer else None,
    }


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

    Returns None, after a warning, when the directory cannot be created or
    written. Other export errors are also warned and swallowed so a portfolio
    run is never aborted by the signal file.

    ``warnings``, when not None, is written as a top-level array. Omit it to
    keep the original envelope (callers that have nothing to flag).
    """
    out_dir = os.environ.get("SIGNALS_OUT_DIR", DEFAULT_SIGNALS_DIR)
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


def pipeline_dir() -> str:
    """``PIPELINE_DIR``, else the parent of ``SIGNALS_OUT_DIR``."""
    explicit = os.environ.get("PIPELINE_DIR")
    if explicit:
        return explicit
    signals = os.environ.get("SIGNALS_OUT_DIR", DEFAULT_SIGNALS_DIR)
    return os.path.dirname(os.path.abspath(signals))


def entry_state_path(portfolio_meta) -> str:
    """Entry state of this portfolio: ``ENTRY_STATE_FILE``, else
    ``<pipeline dir>/state/entry_state_<optimizer>_<run_ts stamp>.json``."""
    explicit = os.environ.get("ENTRY_STATE_FILE")
    if explicit:
        return explicit
    key = portfolio_key(portfolio_meta) or "hardcoded_fallback"
    return os.path.join(pipeline_dir(), "state", f"entry_state_{key}.json")


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
    as ``tranche_weight``). Pending cash decisions on that signal are applied
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
    if isinstance(pending_day, int) and not isinstance(pending_day, bool):
        updated["dia_ciclo"] = pending_day
        updated["ciclo_cerrado"] = pending_day >= int(cycle_length)
    pending_cycle = updated.get("pending_cycle")
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


def stage_pending_entry(estado, run_ts, cycle_day, cycle, targets=None, cash=None, decisions=None):
    """Remember the signal that is waiting for fills. Does not mark invested."""
    updated = copy.deepcopy(estado or {})
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


def suggest_cycle_day(estado, cycle_length: int = 5) -> int:
    """Next cycle day from the last *executed* state. Does not write the file."""
    estado = estado or {}
    if estado.get("ultima_actualizacion") is None or estado.get("ciclo_cerrado"):
        return 1
    try:
        dia = int(estado.get("dia_ciclo") or 1)
    except (TypeError, ValueError):
        dia = 1
    if dia < 1:
        dia = 1
    return min(dia + 1, int(cycle_length))


def resolve_cycle_day(explicit, estado, cycle_length: int = 5):
    """Return ``(day, warning)``. Blank explicit input uses ``suggest_cycle_day``."""
    suggested = suggest_cycle_day(estado, cycle_length)
    if explicit is None or (isinstance(explicit, str) and explicit.strip() == ""):
        return suggested, None
    try:
        dia = int(explicit)
    except (TypeError, ValueError):
        return suggested, f"invalid cycle day {explicit!r}; using {suggested}"
    if not 1 <= dia <= int(cycle_length):
        return suggested, f"cycle day {dia} outside 1..{cycle_length}; using {suggested}"
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
