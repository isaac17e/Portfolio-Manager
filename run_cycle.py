"""Run the Portfolio-Manager cycle with one command.

Daily mode validates the portfolio file and runs, in order,
``fundamental_analysis``, ``portfolio_risk_score_leverage``,
``portfolio_gex_field`` (``--once`` and ``HEADLESS=1``), ``portfolio_vix``
(``--no-show``), and ``entry_signal_tool``. Weekly mode runs only
``active_management``, and only on the first NYSE session of the ISO week
that has not already succeeded.

Each step is a subprocess of this interpreter (``sys.executable``). Stdin is
``DEVNULL``. After a step exits 0, ``<SIGNALS_OUT_DIR>/<script>.json`` must
have been written during that step, with ``portfolio_source`` equal to the
portfolio path and ``portfolio_run_ts`` equal to the portfolio ``run_ts``.
``hardcoded_fallback`` is a failure. The first failure stops the cycle.

Exit codes:
    0  success, weekly not due, skipped after horizon_end, or dry-run
    1  invalid portfolio, step failure, bad signal file, timeout,
       missing NYSE calendar, or a summary/state write error
    2  invalid arguments
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

BOGOTA = ZoneInfo("America/Bogota")
SCHEMA_VERSION = 1
WEIGHT_SUM_TOLERANCE = 1e-4
DEFAULT_TIMEOUT = 1800.0
DEFAULT_PORTFOLIO_FILE = "/workspace/pipeline/portfolio/portfolio_latest.json"
DEFAULT_SIGNALS_DIR = "/workspace/pipeline/signals"
DEFAULT_SUMMARY_DIR = "/workspace/pipeline"
DEFAULT_WEEKLY_STATE = "/workspace/pipeline/state/weekly_last_run.json"

DAILY_STEPS = [
    "fundamental_analysis",
    "portfolio_risk_score_leverage",
    "portfolio_gex_field",
    "portfolio_vix",
    "entry_signal_tool",
]
WEEKLY_STEPS = ["active_management"]
ALL_STEPS = DAILY_STEPS + WEEKLY_STEPS

ROOT = os.path.dirname(os.path.abspath(__file__))

_EXIT_HELP = """
exit codes:
  0  success, weekly not due, skipped after horizon_end, or dry-run
  1  invalid portfolio, step failure, bad/stale signal, timeout,
     missing NYSE calendar, or summary/state write error
  2  invalid arguments

weekly due check (America/Bogota date, or --date): today is an NYSE session,
it is the first session of its ISO week, and this week's weekly cycle has not
already succeeded. A holiday Monday therefore runs on the next session of that
week. --force skips this check and still respects horizon_end.
""".strip()


class UsageError(Exception):
    """Bad arguments that argparse did not already reject."""


class PortfolioError(Exception):
    """The portfolio file failed validation."""


class SignalError(Exception):
    """A step's signal file is missing, stale, or for the wrong portfolio."""


class CalendarUnavailable(Exception):
    """Neither NYSE calendar library can be imported."""


def _now_bogota() -> datetime:
    return datetime.now(BOGOTA).replace(microsecond=0)


def _today_bogota() -> date:
    return datetime.now(BOGOTA).date()


def _invalid(message: str) -> None:
    raise PortfolioError(f"invalid portfolio: {message}")


def atomic_write(path: str, text: str) -> None:
    """Write ``path`` via ``path.tmp`` and ``os.replace``, same as pipeline_io."""
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


def _resolve_path(flag_value: str | None, env_name: str, default: str) -> str:
    if flag_value:
        return os.path.abspath(flag_value)
    env_value = os.environ.get(env_name)
    if env_value:
        return os.path.abspath(env_value)
    return default


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Portfolio-Manager daily or weekly cycle.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_EXIT_HELP,
    )
    parser.add_argument(
        "--portfolio",
        default=os.environ.get("PORTFOLIO_FILE", DEFAULT_PORTFOLIO_FILE),
        help="portfolio JSON (env PORTFOLIO_FILE; "
        f"default {DEFAULT_PORTFOLIO_FILE})",
    )
    parser.add_argument(
        "--signals-dir",
        default=None,
        help=f"signal output directory (env SIGNALS_OUT_DIR; default {DEFAULT_SIGNALS_DIR})",
    )
    parser.add_argument(
        "--summary-dir",
        default=None,
        help=f"cycle summary directory (env CYCLE_SUMMARY_DIR; default {DEFAULT_SUMMARY_DIR})",
    )
    parser.add_argument(
        "--weekly-state",
        default=None,
        help="weekly last-success file "
        f"(env WEEKLY_STATE_FILE; default {DEFAULT_WEEKLY_STATE})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help=f"per-step timeout in seconds (env CYCLE_STEP_TIMEOUT; default {DEFAULT_TIMEOUT:g})",
    )
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Monday routine: only active_management, subject to the NYSE due check",
    )
    parser.add_argument(
        "--date",
        type=_parse_cli_date,
        default=None,
        help="override today as YYYY-MM-DD in America/Bogota (for tests and replays)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="run the weekly cycle even when it is not due; horizon_end still applies",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the plan or the skip reason and write nothing",
    )
    parser.add_argument(
        "--steps",
        default=None,
        help="comma-separated subset of steps, executed in canonical order",
    )
    return parser


def _parse_cli_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"date must be YYYY-MM-DD, got {value!r}"
        ) from exc


def resolve_timeout(args: argparse.Namespace) -> float:
    raw = args.timeout
    if raw is None:
        raw = os.environ.get("CYCLE_STEP_TIMEOUT", str(DEFAULT_TIMEOUT))
    try:
        timeout = float(raw)
    except (TypeError, ValueError) as exc:
        raise UsageError(f"timeout must be a positive number, got {raw!r}") from exc
    if not math.isfinite(timeout) or timeout <= 0:
        raise UsageError(f"timeout must be a positive number, got {raw!r}")
    return timeout


def select_steps(weekly: bool, steps_arg: str | None) -> list[str]:
    if steps_arg is None:
        return list(WEEKLY_STEPS if weekly else DAILY_STEPS)
    names = [part.strip() for part in steps_arg.split(",") if part.strip()]
    if not names:
        raise UsageError("`--steps` is empty")
    unknown = [name for name in names if name not in ALL_STEPS]
    if unknown:
        raise UsageError(
            "unknown step(s): " + ", ".join(unknown)
            + ". Known steps: " + ", ".join(ALL_STEPS)
        )
    selected = set(names)
    return [name for name in ALL_STEPS if name in selected]


def load_portfolio_file(path: str) -> dict:
    """Validate a portfolio file (contract section 1) and return its fields.

    Weights must sum to about 1 (absolute tolerance ``WEIGHT_SUM_TOLERANCE``).
    ``tickers`` and ``weights`` must contain the same names. ``run_ts`` and
    ``optimizer`` are required. ``horizon_end`` is a date or null.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except FileNotFoundError:
        _invalid(f"file not found ({path})")
    except OSError as exc:
        _invalid(f"could not read {path}: {exc}")
    except json.JSONDecodeError as exc:
        _invalid(f"not valid JSON ({path}): {exc}")

    if not isinstance(payload, dict):
        _invalid(f"not a JSON object ({path})")

    version = payload.get("schema_version")
    if isinstance(version, bool) or version != SCHEMA_VERSION:
        _invalid(f"schema_version must be 1, got {version!r}")

    optimizer = payload.get("optimizer")
    if not isinstance(optimizer, str) or not optimizer.strip():
        _invalid("optimizer is missing")

    run_ts = payload.get("run_ts")
    if not isinstance(run_ts, str) or not run_ts.strip():
        _invalid("run_ts is missing")
    try:
        datetime.fromisoformat(run_ts)
    except ValueError as exc:
        _invalid(f"run_ts is not a valid ISO timestamp ({run_ts!r}): {exc}")

    weights = _parse_weights(payload.get("weights"))
    tickers = _parse_tickers(payload.get("tickers"), weights)
    horizon_end = _parse_horizon_end(payload)

    return {
        "path": path,
        "optimizer": optimizer,
        "run_ts": run_ts,
        "horizon_end": horizon_end,
        "tickers": tickers,
        "weights": weights,
    }


def _parse_weights(raw) -> dict:
    if not isinstance(raw, dict) or not raw:
        _invalid("weights must be a non-empty object")
    weights = {}
    for key, value in raw.items():
        ticker = str(key).strip()
        if not ticker:
            _invalid("weights contain an empty ticker")
        if ticker in weights:
            _invalid(f"duplicate ticker {ticker}")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            _invalid(f"weight for {ticker} is not a number")
        number = float(value)
        if not math.isfinite(number) or number < 0:
            _invalid(f"weight for {ticker} must be a finite number >= 0")
        weights[ticker] = number
    if not any(value > 0 for value in weights.values()):
        _invalid("weights have no positive holding")
    total = math.fsum(weights.values())
    if abs(total - 1.0) > WEIGHT_SUM_TOLERANCE:
        _invalid(
            f"weights sum to {total:.6f}, expected ~1 "
            f"(tolerance {WEIGHT_SUM_TOLERANCE})"
        )
    return weights


def _parse_tickers(raw, weights: dict) -> list[str]:
    if not isinstance(raw, list) or not raw:
        _invalid("tickers must be a non-empty list matching the weights")
    tickers = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            _invalid("tickers must be non-empty strings")
        ticker = item.strip()
        if ticker in tickers:
            _invalid(f"duplicate ticker {ticker}")
        tickers.append(ticker)
    only_tickers = sorted(set(tickers) - set(weights))
    only_weights = sorted(set(weights) - set(tickers))
    if only_tickers or only_weights:
        _invalid(
            "tickers and weights are inconsistent: "
            f"only in tickers {only_tickers or '[]'}; "
            f"only in weights {only_weights or '[]'}"
        )
    return tickers


def _parse_horizon_end(payload: dict) -> date | None:
    if "horizon_end" not in payload or payload.get("horizon_end") is None:
        return None
    raw = payload.get("horizon_end")
    if not isinstance(raw, str):
        _invalid(f"horizon_end must be YYYY-MM-DD or null, got {raw!r}")
    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError as exc:
        raise PortfolioError(
            f"invalid portfolio: horizon_end must be YYYY-MM-DD or null, got {raw!r}"
        ) from exc


def build_command(script: str) -> list[str]:
    """Command for one step. GEX is one-shot; VIX does not open a window."""
    command = [sys.executable, os.path.join(ROOT, f"{script}.py")]
    if script == "portfolio_gex_field":
        command.append("--once")
    elif script == "portfolio_vix":
        command.append("--no-show")
    return command


def step_environment(portfolio_path: str, signals_dir: str, script: str) -> dict:
    """Parent environment plus the portfolio and signal locations for this step."""
    env = os.environ.copy()
    env["PORTFOLIO_FILE"] = portfolio_path
    env["SIGNALS_OUT_DIR"] = signals_dir
    env["PYTHONUNBUFFERED"] = "1"
    if script == "portfolio_gex_field":
        env["HEADLESS"] = "1"
    return env


def nyse_session_dates(start: date, end: date) -> list[date]:
    """NYSE session dates in ``[start, end]``, inclusive.

    Uses ``pandas_market_calendars`` when it is installed, otherwise
    ``exchange_calendars``. Both ship the calendar locally. A missing library
    raises ``CalendarUnavailable`` with an install hint.
    """
    try:
        import pandas_market_calendars as mcal
    except ImportError:
        mcal = None
    if mcal is not None:
        schedule = mcal.get_calendar("NYSE").schedule(
            start_date=start.isoformat(),
            end_date=end.isoformat(),
        )
        if schedule is None or len(schedule.index) == 0:
            return []
        return [stamp.date() for stamp in schedule.index]

    try:
        import exchange_calendars as xcals
        import pandas as pd
    except ImportError as exc:
        raise CalendarUnavailable(
            "NYSE calendar library is not installed. "
            "Install pandas_market_calendars or exchange_calendars "
            "(pip install -r requirements.txt)."
        ) from exc

    calendar = xcals.get_calendar("XNYS")
    sessions = calendar.sessions_in_range(pd.Timestamp(start), pd.Timestamp(end))
    return [stamp.date() for stamp in sessions]


def _iso_week(day: date) -> tuple[int, int]:
    iso = day.isocalendar()
    return (iso[0], iso[1])


def read_weekly_state(path: str) -> tuple[dict | None, str | None]:
    """Return ``(state, warning)``. A missing file is no prior run."""
    if not os.path.isfile(path):
        return None, None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return None, (
            f"weekly state file is unreadable ({path}: {exc}); "
            "treating it as no prior run"
        )
    if not isinstance(payload, dict):
        return None, (
            f"weekly state file is not a JSON object ({path}); "
            "treating it as no prior run"
        )
    return payload, None


def already_ran_this_week(state: dict | None, as_of: date) -> bool:
    if not state:
        return False
    raw = state.get("last_run_date")
    if not isinstance(raw, str):
        return False
    try:
        previous = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        return False
    return _iso_week(previous) == _iso_week(as_of)


def weekly_due(as_of: date, state_path: str) -> tuple[bool, str | None, str | None]:
    """Return ``(due, reason, warning)``.

    Reason is ``non_trading_day``, ``not_first_trading_day_of_week``, or
    ``already_ran_this_week``. The ISO week is Monday–Sunday of ``as_of``.
    Its first NYSE session is the scheduled day (Tuesday when Monday is closed).
    """
    monday = as_of - timedelta(days=as_of.weekday())
    sunday = monday + timedelta(days=6)
    sessions = nyse_session_dates(monday, sunday)
    state, warning = read_weekly_state(state_path)
    if as_of not in set(sessions):
        return False, "non_trading_day", warning
    if not sessions or as_of != sessions[0]:
        return False, "not_first_trading_day_of_week", warning
    if already_ran_this_week(state, as_of):
        return False, "already_ran_this_week", warning
    return True, None, warning


def _kill_process_group(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass


def _as_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _run_command(command: list[str], env: dict, timeout: float):
    """Run ``command``. Return ``(exit_code, stdout, stderr, timed_out)``."""
    proc = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        partial_out = _as_text(exc.stdout)
        partial_err = _as_text(exc.stderr)
        _kill_process_group(proc)
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
        return None, partial_out + _as_text(stdout), partial_err + _as_text(stderr), True
    return proc.returncode, _as_text(stdout), _as_text(stderr), False


def _tail(text: str, lines: int = 40, max_chars: int = 4000) -> str:
    if not text:
        return ""
    chosen = "\n".join(text.splitlines()[-lines:])
    if len(chosen) > max_chars:
        chosen = chosen[-max_chars:]
    return chosen


def _with_tail(message: str, stderr: str) -> str:
    tail = _tail(stderr)
    if not tail:
        return message
    return f"{message}\n--- stderr (tail) ---\n{tail}"


def verify_signal(
    path: str,
    script: str,
    portfolio_path: str,
    portfolio_run_ts: str,
    step_start: datetime,
) -> dict:
    """Accept a signal only if this step wrote it for this portfolio."""
    if not os.path.isfile(path):
        raise SignalError(f"{script}: signal file was not written ({path})")

    mtime = datetime.fromtimestamp(os.path.getmtime(path), BOGOTA).replace(microsecond=0)
    if mtime < step_start:
        raise SignalError(
            f"{script}: stale signal file {path} "
            f"(mtime {mtime.isoformat()} is before the step started at {step_start.isoformat()})"
        )

    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SignalError(f"{script}: signal file is not valid JSON ({path}): {exc}") from exc
    except OSError as exc:
        raise SignalError(f"{script}: could not read signal file ({path}): {exc}") from exc

    if not isinstance(payload, dict):
        raise SignalError(f"{script}: signal file is not a JSON object ({path})")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise SignalError(
            f"{script}: signal schema_version must be 1, got {payload.get('schema_version')!r}"
        )
    if payload.get("script") != script:
        raise SignalError(
            f"{script}: signal file script field is {payload.get('script')!r}"
        )

    source = payload.get("portfolio_source")
    if source == "hardcoded_fallback":
        raise SignalError(f"{script}: portfolio_source is hardcoded_fallback")
    if source != portfolio_path:
        raise SignalError(
            f"{script}: portfolio_source {source!r} does not match portfolio path {portfolio_path!r}"
        )
    got_run_ts = payload.get("portfolio_run_ts")
    if got_run_ts != portfolio_run_ts:
        raise SignalError(
            f"{script}: portfolio_run_ts {got_run_ts!r} does not match "
            f"portfolio run_ts {portfolio_run_ts!r}"
        )

    raw_run_ts = payload.get("run_ts")
    if not isinstance(raw_run_ts, str) or not raw_run_ts:
        raise SignalError(f"{script}: signal run_ts is missing ({path})")
    try:
        run_at = datetime.fromisoformat(raw_run_ts)
    except ValueError as exc:
        raise SignalError(f"{script}: signal run_ts is not ISO ({raw_run_ts!r})") from exc
    if run_at.tzinfo is None:
        run_at = run_at.replace(tzinfo=BOGOTA)
    else:
        run_at = run_at.astimezone(BOGOTA)
    run_at = run_at.replace(microsecond=0)
    if run_at < step_start:
        raise SignalError(
            f"{script}: stale signal file {path} "
            f"(run_ts {run_at.isoformat()} is before the step started at {step_start.isoformat()})"
        )
    return payload


_SCALAR_KEYS = {
    "portfolio_risk_score_leverage": ("target_leverage", "risk_score"),
    "portfolio_vix": ("vix_portfolio",),
    "portfolio_gex_field": ("macro_y", "potential_z", "grad_magnitude", "n_holdings"),
    "fundamental_analysis": ("n_tickers", "n_indicators"),
    "active_management": ("regime", "vol_portfolio", "diversification_ratio"),
}


def _absorb_signal(script: str, payload: dict, scalars: dict, signal_warnings: dict, excluded: dict) -> None:
    data = payload.get("data")
    if not isinstance(data, dict):
        data = {}
    warnings = payload.get("warnings")
    if warnings is None:
        warnings = []
    elif not isinstance(warnings, list):
        warnings = [str(warnings)]
    signal_warnings[script] = warnings
    items = data.get("excluded")
    excluded[script] = items if isinstance(items, list) else []
    for key in _SCALAR_KEYS.get(script, ()):
        if key in data:
            scalars[key] = data[key]
    if script == "entry_signal_tool":
        entries = data.get("entries")
        if not isinstance(entries, list):
            entries = []
        scalars["entries"] = entries
        scalars["n_entries"] = len(entries)
    if script == "active_management":
        rebalances = data.get("rebalances")
        if isinstance(rebalances, list):
            scalars["rebalances"] = rebalances
            scalars["n_rebalances"] = len(rebalances)


def _blank_step(script: str, command: list[str] | None = None) -> dict:
    return {
        "script": script,
        "status": "not_run",
        "duration_seconds": None,
        "exit_code": None,
        "output_file": None,
        "command": command,
        "error": None,
    }


def run_steps(steps: list[str], portfolio: dict, signals_dir: str, timeout: float) -> dict:
    records = []
    failed = None
    scalars: dict = {}
    signal_warnings: dict = {}
    excluded: dict = {}
    for script in steps:
        if failed is not None:
            records.append(_blank_step(script))
            continue
        command = build_command(script)
        record = _blank_step(script, command)

        step_start = _now_bogota()
        started = time.monotonic()
        code, _stdout, stderr, timed_out = _run_command(
            command,
            step_environment(portfolio["path"], signals_dir, script),
            timeout,
        )
        record["duration_seconds"] = round(time.monotonic() - started, 3)
        output = os.path.join(signals_dir, f"{script}.json")
        if timed_out:
            record["status"] = "failed"
            record["error"] = _with_tail(
                f"{script} timed out after {timeout:g}s",
                stderr,
            )
            failed = record
        elif code != 0:
            record["status"] = "failed"
            record["exit_code"] = code
            record["error"] = _with_tail(
                f"{script} failed with exit code {code}",
                stderr,
            )
            failed = record
        else:
            record["exit_code"] = 0
            try:
                payload = verify_signal(
                    output,
                    script,
                    portfolio["path"],
                    portfolio["run_ts"],
                    step_start,
                )
            except SignalError as exc:
                record["status"] = "failed"
                record["error"] = str(exc)
                failed = record
            else:
                record["status"] = "success"
                record["output_file"] = output
                _absorb_signal(script, payload, scalars, signal_warnings, excluded)
        records.append(record)

    return {
        "ok": failed is None,
        "steps": records,
        "failing_step": None if failed is None else failed["script"],
        "error": None if failed is None else failed["error"],
        "scalars": scalars,
        "signal_warnings": signal_warnings,
        "excluded": excluded,
    }


def _portfolio_view(portfolio: dict) -> dict:
    horizon = portfolio.get("horizon_end")
    if isinstance(horizon, date):
        horizon = horizon.isoformat()
    return {
        "path": portfolio.get("path"),
        "optimizer": portfolio.get("optimizer"),
        "run_ts": portfolio.get("run_ts"),
        "horizon_end": horizon,
    }


def make_summary(
    *,
    mode: str,
    status: str,
    as_of: date,
    portfolio: dict,
    forced: bool,
    steps: list,
    scalars: dict | None = None,
    signal_warnings: dict | None = None,
    excluded: dict | None = None,
    warnings: list | None = None,
    failing_step: str | None = None,
    error: str | None = None,
    not_due_reason: str | None = None,
    message: str | None = None,
    run_ts: datetime | None = None,
) -> dict:
    stamp = run_ts or _now_bogota()
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": mode,
        "status": status,
        "run_ts": stamp.isoformat(),
        "as_of_date": as_of.isoformat(),
        "forced": bool(forced),
        "portfolio": _portfolio_view(portfolio),
        "failing_step": failing_step,
        "not_due_reason": not_due_reason,
        "message": message,
        "error": error,
        "warnings": list(warnings or []),
        "steps": steps,
        "scalars": dict(scalars or {}),
        "signal_warnings": dict(signal_warnings or {}),
        "excluded": dict(excluded or {}),
    }


def _json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def render_summary_text(summary: dict) -> str:
    portfolio = summary.get("portfolio") or {}
    lines = [
        "Portfolio-Manager cycle",
        f"status: {summary.get('status')}",
        f"mode: {summary.get('mode')}",
        f"run_ts: {summary.get('run_ts')}",
        f"as_of_date: {summary.get('as_of_date')}",
        f"forced: {summary.get('forced')}",
        f"message: {summary.get('message') or ''}",
        "",
        f"portfolio: {portfolio.get('path')}",
        f"optimizer: {portfolio.get('optimizer')}",
        f"portfolio_run_ts: {portfolio.get('run_ts')}",
        f"horizon_end: {portfolio.get('horizon_end')}",
        "",
        "steps:",
    ]
    for step in summary.get("steps") or []:
        duration = step.get("duration_seconds")
        duration_text = "-" if duration is None else f"{duration:.3f}s"
        exit_code = step.get("exit_code")
        exit_text = "-" if exit_code is None else str(exit_code)
        lines.append(
            f"  {step.get('script')}  {step.get('status')}  {duration_text}  exit {exit_text}"
        )
        if step.get("output_file"):
            lines.append(f"    output: {step['output_file']}")
        if step.get("error"):
            lines.append(f"    error: {step['error']}")
    lines.append("")
    lines.append("scalars:")
    scalars = summary.get("scalars") or {}
    if not scalars:
        lines.append("  (none)")
    for key, value in scalars.items():
        if key in ("entries", "rebalances") and isinstance(value, list):
            lines.append(f"  {key}:")
            if not value:
                lines.append("    (none)")
            for item in value:
                if isinstance(item, dict):
                    bits = [f"{item.get('order', '')}".strip(), str(item.get("ticker", ""))]
                    action = item.get("action")
                    if action:
                        bits.append(str(action))
                    detail = " ".join(bit for bit in bits if bit)
                    lines.append(f"    {detail}")
                else:
                    lines.append(f"    {item}")
        else:
            lines.append(f"  {key}: {value}")
    lines.append("")
    lines.append("warnings:")
    wrote_warning = False
    for warning in summary.get("warnings") or []:
        lines.append(f"  (cycle) {warning}")
        wrote_warning = True
    for script, warnings in (summary.get("signal_warnings") or {}).items():
        for warning in warnings or []:
            lines.append(f"  {script}: {warning}")
            wrote_warning = True
    if not wrote_warning:
        lines.append("  (none)")
    lines.append("")
    lines.append("excluded:")
    wrote_excluded = False
    for script, items in (summary.get("excluded") or {}).items():
        for item in items or []:
            if isinstance(item, dict):
                lines.append(
                    f"  {script}: {item.get('ticker')}: {item.get('reason')}"
                )
            else:
                lines.append(f"  {script}: {item}")
            wrote_excluded = True
    if not wrote_excluded:
        lines.append("  (none)")
    lines.append("")
    lines.append(f"failing_step: {summary.get('failing_step')}")
    lines.append(f"not_due_reason: {summary.get('not_due_reason')}")
    error = summary.get("error")
    lines.append("error:")
    lines.append(error if error else "  (none)")
    lines.append("")
    return "\n".join(lines)


def emit_summary(summary_dir: str, summary: dict) -> None:
    os.makedirs(summary_dir, exist_ok=True)
    run_at = datetime.fromisoformat(summary["run_ts"])
    stamp = run_at.strftime("%Y%m%dT%H%M%S")
    body = json.dumps(_json_safe(summary), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    text = render_summary_text(summary)
    names = (
        "cycle_summary_latest.json",
        f"cycle_summary_{stamp}.json",
        "cycle_summary_latest.txt",
        f"cycle_summary_{stamp}.txt",
    )
    payloads = (body, body, text, text)
    for name, payload in zip(names, payloads):
        atomic_write(os.path.join(summary_dir, name), payload)


def write_weekly_state(path: str, as_of: date, portfolio: dict, run_ts: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    iso_year, iso_week = _iso_week(as_of)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "last_run_date": as_of.isoformat(),
        "iso_year": iso_year,
        "iso_week": iso_week,
        "last_run_ts": run_ts,
        "portfolio_path": portfolio.get("path"),
        "portfolio_run_ts": portfolio.get("run_ts"),
    }
    atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _preview_steps(steps: list[str]) -> list[dict]:
    return [_blank_step(script) for script in steps]


def _print_plan(mode: str, as_of: date, portfolio: dict, steps: list[str], signals_dir: str, summary_dir: str, timeout: float, warnings: list[str]) -> None:
    print(
        f"dry-run mode={mode} as_of={as_of.isoformat()} "
        f"optimizer={portfolio.get('optimizer')} "
        f"portfolio_run_ts={portfolio.get('run_ts')} "
        f"horizon_end={_portfolio_view(portfolio).get('horizon_end')}"
    )
    print(f"portfolio={portfolio.get('path')}")
    print(f"signals_dir={signals_dir}")
    print(f"summary_dir={summary_dir}")
    print(f"timeout={timeout:g}")
    for warning in warnings:
        print(f"warning: {warning}")
    print("steps:")
    for index, script in enumerate(steps, start=1):
        command = build_command(script)
        env = step_environment(portfolio["path"], signals_dir, script)
        print(f"  {index} {script}")
        print("    " + " ".join(command))
        extra = f"PORTFOLIO_FILE={env['PORTFOLIO_FILE']} SIGNALS_OUT_DIR={env['SIGNALS_OUT_DIR']}"
        if script == "portfolio_gex_field":
            extra += f" HEADLESS={env['HEADLESS']}"
        print(f"    env {extra}")


def _emit_or_report(summary_dir: str, summary: dict) -> str | None:
    try:
        emit_summary(summary_dir, summary)
    except OSError as exc:
        print(f"could not write cycle summary under {summary_dir}: {exc}", file=sys.stderr)
        return str(exc)
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return 0
        return code if isinstance(code, int) else 2

    try:
        timeout = resolve_timeout(args)
        steps = select_steps(bool(args.weekly), args.steps)
    except UsageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    as_of = args.date or _today_bogota()
    mode = "weekly" if args.weekly else "daily"
    portfolio_path = os.path.abspath(args.portfolio)
    signals_dir = _resolve_path(args.signals_dir, "SIGNALS_OUT_DIR", DEFAULT_SIGNALS_DIR)
    summary_dir = _resolve_path(args.summary_dir, "CYCLE_SUMMARY_DIR", DEFAULT_SUMMARY_DIR)
    state_path = _resolve_path(args.weekly_state, "WEEKLY_STATE_FILE", DEFAULT_WEEKLY_STATE)
    empty_portfolio = {
        "path": portfolio_path,
        "optimizer": None,
        "run_ts": None,
        "horizon_end": None,
    }

    try:
        portfolio = load_portfolio_file(portfolio_path)
    except PortfolioError as exc:
        message = str(exc)
        summary = make_summary(
            mode=mode,
            status="failed",
            as_of=as_of,
            portfolio=empty_portfolio,
            forced=bool(args.force),
            steps=[],
            error=message,
            message=message,
        )
        _emit_or_report(summary_dir, summary)
        print(message, file=sys.stderr)
        return 1

    cycle_warnings: list[str] = []
    if args.weekly:
        horizon = portfolio["horizon_end"]
        if horizon is None:
            cycle_warnings.append("horizon_end is null; running the weekly cycle anyway")
        elif as_of > horizon:
            message = (
                f"skipped_after_horizon: {as_of.isoformat()} is after "
                f"horizon_end {horizon.isoformat()}"
            )
            if args.dry_run:
                print(message)
                return 0
            summary = make_summary(
                mode=mode,
                status="skipped_after_horizon",
                as_of=as_of,
                portfolio=portfolio,
                forced=bool(args.force),
                steps=_preview_steps(steps),
                warnings=[],
                message=message,
            )
            _emit_or_report(summary_dir, summary)
            print(message)
            return 0

        if args.force:
            cycle_warnings.append("due check bypassed by --force")
        else:
            try:
                due, reason, state_warning = weekly_due(as_of, state_path)
            except CalendarUnavailable as exc:
                message = str(exc)
                summary = make_summary(
                    mode=mode,
                    status="failed",
                    as_of=as_of,
                    portfolio=portfolio,
                    forced=False,
                    steps=_preview_steps(steps),
                    warnings=cycle_warnings,
                    error=message,
                    message=message,
                )
                _emit_or_report(summary_dir, summary)
                print(message, file=sys.stderr)
                return 1
            if state_warning:
                cycle_warnings.append(state_warning)
            if not due:
                message = f"not_due: {reason} ({as_of.isoformat()})"
                if args.dry_run:
                    print(message)
                    return 0
                summary = make_summary(
                    mode=mode,
                    status="not_due",
                    as_of=as_of,
                    portfolio=portfolio,
                    forced=False,
                    steps=_preview_steps(steps),
                    warnings=cycle_warnings,
                    not_due_reason=reason,
                    message=message,
                )
                _emit_or_report(summary_dir, summary)
                print(message)
                return 0

    if args.dry_run:
        _print_plan(
            mode, as_of, portfolio, steps, signals_dir, summary_dir, timeout, cycle_warnings,
        )
        return 0

    outcome = run_steps(steps, portfolio, signals_dir, timeout)
    status = "success" if outcome["ok"] else "failed"
    message = "cycle success" if outcome["ok"] else outcome["error"]
    summary = make_summary(
        mode=mode,
        status=status,
        as_of=as_of,
        portfolio=portfolio,
        forced=bool(args.force),
        steps=outcome["steps"],
        scalars=outcome["scalars"],
        signal_warnings=outcome["signal_warnings"],
        excluded=outcome["excluded"],
        warnings=cycle_warnings,
        failing_step=outcome["failing_step"],
        error=None if outcome["ok"] else outcome["error"],
        message=message,
    )
    write_error = _emit_or_report(summary_dir, summary)
    if write_error:
        return 1

    if outcome["ok"] and args.weekly:
        try:
            write_weekly_state(state_path, as_of, portfolio, summary["run_ts"])
        except OSError as exc:
            message = f"could not write weekly state file ({state_path}): {exc}"
            summary["status"] = "failed"
            summary["failing_step"] = "weekly_state"
            summary["error"] = message
            summary["message"] = message
            _emit_or_report(summary_dir, summary)
            print(message, file=sys.stderr)
            return 1

    if not outcome["ok"]:
        print(outcome["error"], file=sys.stderr)
        print(f"cycle failed; summary: {os.path.join(summary_dir, 'cycle_summary_latest.json')}", file=sys.stderr)
        return 1

    print(
        f"cycle success mode={mode} "
        f"summary={os.path.join(summary_dir, 'cycle_summary_latest.json')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
