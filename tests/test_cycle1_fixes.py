"""No-network tests for ticker mapping, fills gating, Polygon backoff, and GEX --once."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from unittest import mock

import pipeline_io
import polygon_client
from polygon_client import PolygonClient, PolygonError, retry_backoff_seconds
from portfolio_gex_field import gex_headless_requested
from tickers import (
    has_us_options,
    mapping,
    no_us_options_reason,
    to_capital_epic,
    to_polygon,
    to_yahoo,
)


class _Resp:
    def __init__(self, status, headers=None, body=None, text="err"):
        self.status_code = status
        self.headers = headers or {}
        self._body = {} if body is None else body
        self.text = text

    def json(self):
        return self._body


def _estado(pct=0.2, day=1, pending="2026-10-05T16:40:12-05:00", target=0.12):
    return {
        "ciclo": 1,
        "dia_ciclo": day,
        "ciclo_cerrado": False,
        "ultima_actualizacion": "2026-10-05",
        "pending_signal_run_ts": pending,
        "pending_cycle_day": 2,
        "pending_cycle": 1,
        "pending_targets": {"GLD": target},
        "pending_cash": {"KO": 0.4},
        "pending_decisions": {"GLD": "ENTRAR", "KO": "CASH"},
        "activos": {
            "GLD": {"pct_ya_invertido": pct, "pct_cash_consolidado": 0.0, "decision_final": None},
            "KO": {"pct_ya_invertido": 0.1, "pct_cash_consolidado": 0.0, "decision_final": None},
        },
    }


def _fills(run_ts, status="filled", weight=0.06, ticker="GLD"):
    return {
        "schema_version": 1,
        "signal_run_ts": run_ts,
        "executed_ts": "2026-10-06T15:00:00-05:00",
        "fills": [{
            "ticker": ticker,
            "action": "BUY",
            "filled_weight": weight,
            "filled_qty": 10,
            "price": 180.0,
            "deal_id": "abc",
            "status": status,
        }],
    }


class TickerMappingTests(unittest.TestCase):
    def test_class_share_yahoo_polygon_and_capital(self):
        for canonical in ("BRK-B", "BRK.B", "brk-b"):
            forms = mapping(canonical)
            self.assertEqual(forms["yahoo"], "BRK-B")
            self.assertEqual(forms["polygon"], "BRK.B")
            self.assertEqual(forms["capital_epic"], "BRK.B")
            self.assertFalse(forms["capital_epic_verified"])
            self.assertTrue(forms["has_us_options"])
            self.assertIsNone(forms["us_options_reason"])
        self.assertEqual(to_yahoo("BRK.B"), "BRK-B")
        self.assertEqual(to_polygon("BRK-B"), "BRK.B")
        self.assertEqual(to_capital_epic("BRK-B"), "BRK.B")

    def test_toronto_suffix_has_no_us_options(self):
        forms = mapping("RY.TO")
        self.assertEqual(forms["yahoo"], "RY.TO")
        self.assertEqual(forms["polygon"], "RY.TO")
        self.assertEqual(to_capital_epic("RY.TO"), "RY")
        self.assertFalse(has_us_options("RY.TO"))
        self.assertIn(".TO", no_us_options_reason("ry.to"))
        self.assertEqual(to_yahoo("BRK.B.TO"), "BRK-B.TO")
        self.assertEqual(to_polygon("BRK-B.TO"), "BRK.B.TO")
        self.assertFalse(has_us_options("BRK-B.TO"))

    def test_plain_us_ticker_is_unchanged(self):
        self.assertEqual(to_yahoo("SPY"), "SPY")
        self.assertEqual(to_polygon("SPY"), "SPY")
        self.assertTrue(has_us_options("GLD"))

    def test_mapping_is_idempotent(self):
        self.assertEqual(to_polygon(to_polygon("BRK-B")), "BRK.B")
        self.assertEqual(to_yahoo(to_yahoo("BRK.B")), "BRK-B")
        self.assertEqual(to_yahoo(to_yahoo("RY.TO")), "RY.TO")


class FillsGatingTests(unittest.TestCase):
    def test_matching_fill_advances_weight_and_cash_and_day(self):
        estado = _estado(pct=0.25, target=0.12)
        updated, applied = pipeline_io.apply_entry_fills(estado, _fills(estado["pending_signal_run_ts"]))
        self.assertTrue(applied)
        self.assertAlmostEqual(updated["activos"]["GLD"]["pct_ya_invertido"], 0.25 + 0.06 / 0.12)
        self.assertEqual(updated["activos"]["GLD"]["decision_final"], "ENTRAR")
        self.assertEqual(updated["activos"]["KO"]["pct_cash_consolidado"], 0.4)
        self.assertEqual(updated["activos"]["KO"]["decision_final"], "CASH")
        self.assertEqual(updated["dia_ciclo"], 2)
        self.assertFalse(updated["ciclo_cerrado"])
        self.assertIsNone(updated["pending_signal_run_ts"])
        self.assertEqual(estado["activos"]["GLD"]["pct_ya_invertido"], 0.25)

    def test_mismatched_run_ts_does_not_advance(self):
        estado = _estado()
        updated, applied = pipeline_io.apply_entry_fills(estado, _fills("other-ts"))
        self.assertFalse(applied)
        self.assertIs(updated, estado)
        self.assertEqual(estado["activos"]["GLD"]["pct_ya_invertido"], 0.2)
        self.assertEqual(estado["pending_signal_run_ts"], "2026-10-05T16:40:12-05:00")

    def test_rejected_fill_does_not_change_weight_but_confirms_the_signal(self):
        estado = _estado(pct=0.2)
        updated, applied = pipeline_io.apply_entry_fills(
            estado, _fills(estado["pending_signal_run_ts"], status="rejected")
        )
        self.assertTrue(applied)
        self.assertEqual(updated["activos"]["GLD"]["pct_ya_invertido"], 0.2)
        self.assertEqual(updated["dia_ciclo"], 2)

    def test_partial_status_counts(self):
        estado = _estado(pct=0.0, target=0.10)
        updated, applied = pipeline_io.apply_entry_fills(
            estado, _fills(estado["pending_signal_run_ts"], status="partial", weight=0.05)
        )
        self.assertTrue(applied)
        self.assertAlmostEqual(updated["activos"]["GLD"]["pct_ya_invertido"], 0.5)

    def test_staging_a_signal_does_not_mark_invested(self):
        estado = _estado(pct=0.2, day=1)
        staged = pipeline_io.stage_pending_entry(
            estado, "2026-10-06T12:00:00-05:00", 3, 1, {"GLD": 0.12}, {"KO": 0.4}, {"KO": "CASH"}
        )
        self.assertEqual(staged["activos"]["GLD"]["pct_ya_invertido"], 0.2)
        self.assertEqual(staged["dia_ciclo"], 1)
        self.assertEqual(staged["pending_signal_run_ts"], "2026-10-06T12:00:00-05:00")
        self.assertEqual(staged["pending_cycle_day"], 3)
        self.assertEqual(estado["pending_cycle_day"], 2)

    def test_cycle_day_defaults_and_invested_parse(self):
        fresh = {"ultima_actualizacion": None, "dia_ciclo": 1, "ciclo_cerrado": False, "ciclo": 1}
        self.assertEqual(pipeline_io.suggest_cycle_day(fresh), 1)
        self.assertEqual(pipeline_io.resolve_cycle_day(None, fresh)[0], 1)
        day, warn = pipeline_io.resolve_cycle_day("9", {"ultima_actualizacion": "2026-10-05", "dia_ciclo": 2})
        self.assertEqual(day, 3)
        self.assertIsNotNone(warn)
        day, warn = pipeline_io.resolve_cycle_day("4", {"ultima_actualizacion": "2026-10-05", "dia_ciclo": 2})
        self.assertEqual(day, 4)
        self.assertIsNone(warn)
        closed = {"ultima_actualizacion": "2026-10-05", "dia_ciclo": 5, "ciclo_cerrado": True, "ciclo": 2}
        self.assertEqual(pipeline_io.suggest_cycle_day(closed), 1)
        self.assertEqual(pipeline_io.signal_cycle_number(closed, 1), 3)

        parsed, warns = pipeline_io.parse_invested_overrides("40", ["GLD", "KO"])
        self.assertEqual(parsed, {"GLD": 0.4, "KO": 0.4})
        self.assertEqual(warns, [])
        parsed, warns = pipeline_io.parse_invested_overrides("GLD=40,KO=0.25", ["GLD", "KO"])
        self.assertEqual(parsed["GLD"], 0.4)
        self.assertEqual(parsed["KO"], 0.25)
        parsed, _ = pipeline_io.parse_invested_overrides('{"GLD": "10%"}', ["GLD", "KO"])
        self.assertEqual(parsed, {"GLD": 0.1})
        self.assertIsNone(pipeline_io.parse_invested_overrides(None, ["GLD"])[0])

    def test_locate_prefers_named_file_then_newest_fills(self):
        with tempfile.TemporaryDirectory() as tmp:
            older = Path(tmp) / "fills_old.json"
            newer = Path(tmp) / "fills_new.json"
            named = Path(tmp) / "entry_signal_tool_fills.json"
            older.write_text("{}", encoding="utf-8")
            newer.write_text("{}", encoding="utf-8")
            os.utime(older, (1_000, 1_000))
            os.utime(newer, (2_000, 2_000))
            self.assertEqual(pipeline_io.locate_fills_file(directory=tmp), str(newer))
            named.write_text("{}", encoding="utf-8")
            self.assertEqual(pipeline_io.locate_fills_file(directory=tmp), str(named))

            named.write_text(json.dumps(_fills("ts-1")), encoding="utf-8")
            loaded = pipeline_io.load_fills(directory=tmp)
            self.assertEqual(loaded["signal_run_ts"], "ts-1")
            named.write_text(json.dumps({"schema_version": 2, "signal_run_ts": "x", "fills": []}), encoding="utf-8")
            self.assertIsNone(pipeline_io.load_fills(directory=tmp))

    def test_export_warnings_are_optional(self):
        frozen = datetime(2026, 10, 5, 16, 40, 12, tzinfo=pipeline_io.BOGOTA)
        meta = {
            "weights": {"GLD": 1.0},
            "portfolio_source": "hardcoded_fallback",
            "portfolio_run_ts": None,
            "portfolio_optimizer": None,
        }
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": tmp}):
                with mock.patch.object(pipeline_io, "_now_bogota", return_value=frozen):
                    pipeline_io.export_signals("entry_signal_tool", {"excluded": []}, meta)
                    pipeline_io.export_signals(
                        "portfolio_vix", {"excluded": [{"ticker": "RY.TO", "reason": "no US-listed options"}]},
                        meta, warnings=["RY.TO: no US-listed options"],
                    )
            plain = json.loads((Path(tmp) / "entry_signal_tool.json").read_text(encoding="utf-8"))
            flagged = json.loads((Path(tmp) / "portfolio_vix.json").read_text(encoding="utf-8"))
        self.assertNotIn("warnings", plain)
        self.assertEqual(flagged["warnings"], ["RY.TO: no US-listed options"])
        self.assertEqual(flagged["data"]["excluded"][0]["ticker"], "RY.TO")


class PolygonBackoffTests(unittest.TestCase):
    def test_default_calls_per_minute_is_100(self):
        env = os.environ.copy()
        env.pop("POLYGON_CALLS_PER_MINUTE", None)
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(polygon_client.calls_per_minute_configurado(), 100)

    def test_retry_after_beats_exponential_jitter(self):
        response = _Resp(429, {"Retry-After": "1.5"})
        self.assertEqual(retry_backoff_seconds(1, 4.0, response, jitter=0.9), 1.5)
        when = datetime.now(timezone.utc) + timedelta(seconds=30)
        dated = _Resp(503, {"Retry-After": format_datetime(when, usegmt=True)})
        self.assertAlmostEqual(retry_backoff_seconds(1, 4.0, dated, jitter=0.0), 30, delta=2)
        self.assertEqual(retry_backoff_seconds(2, 4.0, _Resp(500), jitter=0.25), 4.0 * 2 + 2.0)

    def test_client_retries_429_and_5xx_with_mocked_responses(self):
        calls = {"n": 0}

        def fake_get(url, params=None, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                return _Resp(429, {"Retry-After": "1.5"})
            if calls["n"] == 2:
                return _Resp(503)
            return _Resp(200, body={"status": "OK"})

        client = PolygonClient(
            api_key="backoff-test-key", calls_per_minute=10_000,
            retry_wait=1.0, max_retries=4, verbose=False,
        )
        client.session.get = fake_get
        with mock.patch("polygon_client.time.sleep") as sleep, \
                mock.patch("polygon_client.random.random", return_value=0.0):
            body = client.get("/v3/snapshot/options/SPY")
        self.assertEqual(body["status"], "OK")
        self.assertEqual(calls["n"], 3)
        self.assertEqual(sleep.call_args_list[0].args[0], 1.5)
        self.assertEqual(sleep.call_args_list[1].args[0], 2.0)

    def test_client_does_not_retry_400(self):
        client = PolygonClient(
            api_key="backoff-400-key", calls_per_minute=10_000,
            retry_wait=1.0, max_retries=4, verbose=False,
        )
        client.session.get = lambda *args, **kwargs: _Resp(400, text="nope")
        with mock.patch("polygon_client.time.sleep") as sleep:
            with self.assertRaises(PolygonError):
                client.get("/v2/aggs/ticker/SPY/prev")
        sleep.assert_not_called()


class GexHeadlessTests(unittest.TestCase):
    def test_flag_and_env_parsing(self):
        self.assertFalse(gex_headless_requested([], {}))
        self.assertTrue(gex_headless_requested(["--once"], {}))
        self.assertTrue(gex_headless_requested(["--html", "out.html", "--once"], {"HEADLESS": "0"}))
        self.assertTrue(gex_headless_requested([], {"HEADLESS": "1"}))
        self.assertTrue(gex_headless_requested([], {"GEX_ONCE": "yes"}))
        self.assertTrue(gex_headless_requested([], {"HEADLESS": "true"}))
        self.assertFalse(gex_headless_requested([], {"HEADLESS": "0", "GEX_ONCE": "no"}))

    def test_entry_signal_source_has_no_input_prompt(self):
        text = Path("entry_signal_tool.py").read_text(encoding="utf-8")
        self.assertNotIn("input(", text)
        self.assertIn("ENTRY_CYCLE_DAY", text)
        self.assertIn("ENTRY_INVESTED_PCT", text)
        self.assertIn("stage_pending_entry", text)


if __name__ == "__main__":
    unittest.main()
