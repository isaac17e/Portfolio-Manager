"""Shared portfolio input and signal output for the Portfolio-Manager scripts.

Contract: pipeline JSON v1, section 4 (signals). Section 1 describes the
portfolio file this module reads. Writes are atomic and never raise when the
output directory cannot be created or written.
"""

from __future__ import annotations

import json
import math
import os
from datetime import date, datetime
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


def export_signals(script: str, data, portfolio_meta) -> str | None:
    """Write ``<script>.json`` and a timestamped copy. Returns the latest path.

    Returns None, after a warning, when the directory cannot be created or
    written. Other export errors are also warned and swallowed so a portfolio
    run is never aborted by the signal file.
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
