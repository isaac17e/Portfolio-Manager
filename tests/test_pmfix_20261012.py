"""Cumulative fills, real-position active_management, active_management targets in
entry, and the ENTRY-PHASE rule (days 1..5). No network."""

import io
import itertools
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

import drawdown_rotation as dr
import entry_signal_tool as est
import pipeline_io
import run_cycle
from tests import test_run_cycle as trc
from tests.test_drawdown_rotation import _ohlc
from tests.test_review_fixes import _load_active_management
from tests.test_rotation_entry import DAYS, META, OPT, RUN_TS, STAMP, RotationEntryCase

QU = "quadratic_utility"
QU_RUN_TS = "2026-10-08T12:12:53-05:00"
QU_META = {"weights": {}, "portfolio_source": "qu.json", "portfolio_run_ts": QU_RUN_TS,
           "portfolio_optimizer": QU}
QU_STAMP = "20261008T121253"


def fill(ticker, qty, weight=None, action="BUY", **extra):
    row = {"ticker": ticker, "action": action, "filled_qty": qty, "price": 10.0, "status": "filled", **extra}
    if weight is not None:
        row["filled_weight"] = weight
    return row


def doc(signal_run_ts, executed_ts, *fills):
    return {"schema_version": 1, "signal_run_ts": signal_run_ts, "executed_ts": executed_ts,
            "fills": list(fills)}


class ExecDirCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.executions = self.root / "executions"
        self.executions.mkdir()
        patcher = mock.patch.dict(os.environ, {"EXECUTIONS_DIR": str(self.executions)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def put(self, name, payload):
        (self.executions / name).write_text(json.dumps(payload), encoding="utf-8")

    def qu_fills_path(self, suffix=".json"):
        return self.executions / f"fills_{QU}_{QU_STAMP}{suffix}"


class Fix1CumulativeFillsTests(ExecDirCase):
    def qu_day1(self):
        return doc("sig-day1", "2026-10-08T15:00:00-05:00",
                   fill("AMZN", 22.6, 0.10, deal_id="a1"), fill("META", 4.34, 0.05, deal_id="m1"),
                   fill("NTES", 9.4, 0.02, deal_id="n1"), fill("ORLY", 5.9, 0.03, deal_id="o1"),
                   fill("LLY", 1.52, 0.02, deal_id="l1"), fill("AVGO", 3.44, 0.04, deal_id="v1"))

    def qu_day2(self):
        return doc("sig-day2", "2026-10-09T15:00:00-05:00",
                   fill("AVGO", 14.65, 0.17, deal_id="v2"), fill("ORLY", 1.3, 0.01, deal_id="o2"),
                   fill("LLY", 2.05, 0.03, deal_id="l2"))

    def sell_avgo(self):
        return {"schema_version": 1, "script": "active_management", "portfolio_optimizer": QU,
                "portfolio_run_ts": QU_RUN_TS, "executed_ts": "2026-10-12T15:00:00-05:00",
                "fills": [fill("AVGO", 3.44, 0.04, action="SELL", deal_id="s1")]}

    def test_accumulate_keeps_top_level_and_all_tranches(self):
        merged = pipeline_io.accumulate_fills(self.qu_day1(), self.qu_day2())
        self.assertEqual(merged["signal_run_ts"], "sig-day2")
        self.assertEqual(merged["executed_ts"], "2026-10-09T15:00:00-05:00")
        self.assertEqual(merged["schema_version"], 1)
        self.assertEqual(len(merged["fills"]), 9)
        self.assertEqual({f["signal_run_ts"] for f in merged["fills"]}, {"sig-day1", "sig-day2"})
        self.assertEqual([t["signal_run_ts"] for t in merged["tranches"]], ["sig-day1", "sig-day2"])

    def test_accumulate_dedupes_by_deal_id_and_fill_ts(self):
        day2 = self.qu_day2()
        again = pipeline_io.accumulate_fills(pipeline_io.accumulate_fills(self.qu_day1(), day2), day2)
        self.assertEqual(len(again["fills"]), 9)
        same_deal_new_ts = doc("sig-day2", "x", fill("AVGO", 1, 0.01, deal_id="v2", fill_ts="later"))
        self.assertEqual(len(pipeline_io.accumulate_fills(again, same_deal_new_ts)["fills"]), 10)

    def test_writer_appends_instead_of_overwriting(self):
        meta = QU_META
        path = pipeline_io.write_portfolio_fills(meta, self.qu_day1())
        self.assertEqual(Path(path), self.qu_fills_path())
        pipeline_io.write_portfolio_fills(meta, self.qu_day2())
        saved = json.loads(self.qu_fills_path().read_text(encoding="utf-8"))
        self.assertEqual(saved["signal_run_ts"], "sig-day2")
        self.assertEqual(len(saved["fills"]), 9)
        self.assertFalse(list(self.executions.glob("*.tmp")))

    def test_writer_rebuilds_history_from_a_bak(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json.bak", self.qu_day1())
        self.put(f"fills_{QU}_{QU_STAMP}.json", self.qu_day2())
        pipeline_io.write_portfolio_fills(QU_META, doc("sig-day3", "t", fill("AVGO", 1, 0.01, deal_id="v3")))
        saved = json.loads(self.qu_fills_path().read_text(encoding="utf-8"))
        self.assertEqual(len(saved["fills"]), 10)

    def test_net_holdings_are_all_buys_minus_all_sells(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json.bak", self.qu_day1())
        self.put(f"fills_{QU}_{QU_STAMP}.json", self.qu_day2())
        self.put(f"sell_fills_{QU}_{QU_STAMP}.json", self.sell_avgo())
        holdings = pipeline_io.load_portfolio_holdings(QU_META)
        self.assertAlmostEqual(holdings["AVGO"]["bought_qty"], 18.09)
        self.assertAlmostEqual(holdings["AVGO"]["net_qty"], 14.65)
        self.assertAlmostEqual(holdings["AVGO"]["net_weight"], 0.17)
        self.assertAlmostEqual(holdings["AMZN"]["net_qty"], 22.6)
        self.assertAlmostEqual(holdings["META"]["net_qty"], 4.34)
        self.assertAlmostEqual(holdings["NTES"]["net_qty"], 9.4)
        self.assertAlmostEqual(holdings["ORLY"]["net_qty"], 7.2)
        self.assertAlmostEqual(holdings["LLY"]["net_qty"], 3.57)

    def test_old_single_day_file_still_reads(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json", self.qu_day2())
        holdings = pipeline_io.load_portfolio_holdings(QU_META)
        self.assertAlmostEqual(holdings["AVGO"]["net_qty"], 14.65)
        self.assertNotIn("AMZN", holdings)

    def test_copy_of_a_fill_in_a_bak_counts_once(self):
        cumulative = pipeline_io.accumulate_fills(self.qu_day1(), self.qu_day2())
        self.put(f"fills_{QU}_{QU_STAMP}.json", cumulative)
        self.put(f"fills_{QU}_{QU_STAMP}.json.bak", self.qu_day1())
        no_ids = doc("sig-day3", "t", fill("GLD", 2, 0.02), fill("GLD", 2, 0.02))
        self.put(f"fills_{QU}_{QU_STAMP}_copy.json", no_ids)
        self.put(f"fills_{QU}_{QU_STAMP}_copy2.json.bak", no_ids)
        holdings = pipeline_io.load_portfolio_holdings(QU_META)
        self.assertAlmostEqual(holdings["AMZN"]["net_qty"], 22.6)
        self.assertAlmostEqual(holdings["AVGO"]["bought_qty"], 18.09)
        # Two equal fills inside one file are two fills; the copy of the file adds none.
        self.assertAlmostEqual(holdings["GLD"]["net_qty"], 4.0)

    def test_files_of_another_portfolio_are_not_read(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json", self.qu_day2())
        self.put(f"fills_{QU}_extra_{QU_STAMP}.json", self.qu_day1())
        self.put("fills_quadratic_utility_20261009T121253.json", self.qu_day1())
        self.put(f"fills_{QU}_{QU_STAMP}9.json", self.qu_day1())
        holdings = pipeline_io.load_portfolio_holdings(QU_META)
        self.assertEqual(sorted(holdings), ["AVGO", "LLY", "ORLY"])

    def test_qty_only_fill_gets_a_weight_from_capital(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json", doc("s", "t", fill("GLD", 10)))
        self.assertEqual(pipeline_io.load_portfolio_holdings(QU_META)["GLD"]["bought_weight"], 0.0)
        with mock.patch.dict(os.environ, {"PORTFOLIO_CAPITAL": "1000"}):
            self.assertAlmostEqual(pipeline_io.load_portfolio_holdings(QU_META)["GLD"]["net_weight"], 0.1)

    def test_apply_entry_fills_only_counts_the_pending_tranche(self):
        merged = pipeline_io.accumulate_fills(
            doc("sig-1", "t", fill("GLD", 5, 0.05)), doc("sig-2", "t", fill("GLD", 5, 0.05)))
        state = {"pending_signal_run_ts": "sig-2", "pending_targets": {"GLD": 0.5}, "pending_cycle_day": 2,
                 "activos": {"GLD": {"pct_ya_invertido": 0.1, "pct_cash_consolidado": 0.0,
                                     "decision_final": None}}}
        updated, applied = pipeline_io.apply_entry_fills(state, merged)
        self.assertTrue(applied)
        self.assertAlmostEqual(updated["activos"]["GLD"]["pct_ya_invertido"], 0.2)

    def test_entry_and_active_management_read_the_same_net(self):
        self.put(f"fills_{QU}_{QU_STAMP}.json.bak", self.qu_day1())
        self.put(f"fills_{QU}_{QU_STAMP}.json", self.qu_day2())
        self.put(f"sell_fills_{QU}_{QU_STAMP}.json", self.sell_avgo())
        expected = pipeline_io.load_portfolio_holdings(QU_META)
        with mock.patch.object(est, "_PORTFOLIO_META", QU_META):
            self.assertEqual(est.cargar_tenencias(), expected)
        am_source = Path("active_management.py").read_text(encoding="utf-8")
        self.assertIn("holdings = load_portfolio_holdings(_PORTFOLIO_META)", am_source)


class Fix2ActiveManagementRealWeightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.am = _load_active_management()

    def signal(self, holdings):
        table = pd.DataFrame([
            {"Ticker": "AVGO", "Peso_Inicial": 0.30, "Nuevo_Peso": 0.166, "Racional": "r", "Accion": "RECORTAR"},
            {"Ticker": "AMZN", "Peso_Inicial": 0.265, "Nuevo_Peso": 0.188, "Racional": "r", "Accion": "AUMENTAR"},
            {"Ticker": "META", "Peso_Inicial": 0.148, "Nuevo_Peso": 0.178, "Racional": "r", "Accion": "AUMENTAR"},
            {"Ticker": "NTES", "Peso_Inicial": 0.057, "Nuevo_Peso": 0.036, "Racional": "r", "Accion": "RECORTAR"},
            {"Ticker": "CASH", "Peso_Inicial": 0.0, "Nuevo_Peso": 0.0, "Racional": "r",
             "Accion": "RESERVA_TACTICA"},
        ])
        out = self.am["_senal_gestion_activa"]({"tabla_rebalanceo": table, "regimen_riesgo": {}}, holdings)
        return {r["ticker"]: r for r in out["rebalances"]}

    def holdings(self, **weights):
        buys = [fill(t, 10, w) for t, w in weights.items()]
        return pipeline_io.summarize_holdings(doc("s", "t", *buys))

    def test_current_weight_is_the_real_position_not_the_full_target(self):
        rows = self.signal(self.holdings(AVGO=0.18, AMZN=0.15, META=0.10, NTES=0.04))
        self.assertAlmostEqual(rows["AVGO"]["current_weight"], 0.18)
        self.assertAlmostEqual(rows["AVGO"]["original_target_weight"], 0.30)
        self.assertEqual(rows["AVGO"]["action"], "SELL")
        self.assertAlmostEqual(rows["AVGO"]["delta_weight"], 0.166 - 0.18)
        self.assertEqual(rows["AVGO"]["current_weight_source"], "fills")

    def test_under_invested_aumentar_is_not_a_sell(self):
        rows = self.signal(self.holdings(AVGO=0.18, AMZN=0.15, META=0.10, NTES=0.04))
        self.assertEqual(rows["AMZN"]["action"], "BUY")
        self.assertAlmostEqual(rows["AMZN"]["delta_weight"], 0.188 - 0.15)
        self.assertEqual(rows["META"]["action"], "BUY")

    def test_aumentar_above_its_am_target_but_below_the_original_holds(self):
        rows = self.signal(self.holdings(AVGO=0.18, AMZN=0.20, META=0.10, NTES=0.04))
        self.assertEqual(rows["AMZN"]["action"], "HOLD")
        self.assertEqual(rows["AMZN"]["delta_weight"], 0.0)
        self.assertAlmostEqual(rows["AMZN"]["target_weight"], 0.20)

    def test_ticker_without_fills_is_zero_and_never_a_sell(self):
        rows = self.signal(self.holdings(AVGO=0.18))
        self.assertEqual(rows["AMZN"]["current_weight"], 0.0)
        self.assertEqual(rows["AMZN"]["action"], "BUY")
        self.assertEqual(rows["NTES"]["current_weight"], 0.0)
        self.assertNotEqual(rows["NTES"]["action"], "SELL")
        self.assertEqual(rows["NTES"]["action"], "HOLD")

    def test_cash_is_what_is_not_invested(self):
        rows = self.signal(self.holdings(AVGO=0.18, AMZN=0.15, META=0.10, NTES=0.04))
        self.assertAlmostEqual(rows["CASH"]["current_weight"], 1.0 - 0.47)

    def test_position_without_weight_information_keeps_the_target_basis(self):
        holdings = pipeline_io.summarize_holdings(doc("s", "t", fill("AMZN", 10)))
        rows = self.signal(holdings)
        self.assertEqual(rows["AMZN"]["current_weight_source"], "target")
        self.assertAlmostEqual(rows["AMZN"]["current_weight"], 0.265)
        self.assertIsNone(self.signal(holdings)["CASH"]["current_weight_source"] and None)

    def test_without_holdings_the_old_basis_is_kept(self):
        rows = self.signal({})
        self.assertAlmostEqual(rows["AVGO"]["current_weight"], 0.30)
        self.assertEqual(rows["AMZN"]["action"], "SELL")
        self.assertNotIn("current_weight_source", rows["AMZN"])


class EntryPhaseCountTests(ExecDirCase):
    def setUp(self):
        super().setUp()
        patcher = mock.patch.dict(os.environ, {"ENTRY_STATE_FILE": str(self.root / "entry_state.json"),
                                               "CYCLE_DATE": "2026-10-12"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def state(self, **fields):
        (self.root / "entry_state.json").write_text(json.dumps(fields), encoding="utf-8")

    def day(self, today):
        return pipeline_io.entry_phase_info(QU_META, today)

    def test_recorded_start_counts_nyse_sessions(self):
        self.state(entry_start_date="2026-10-08", ultima_actualizacion="2026-10-09")
        # 10-08 Thu, 10-09 Fri, 10-12 Mon (Columbus Day: NYSE open), 10-13, 10-14, 10-15
        days = {d: self.day(d) for d in ("2026-10-08", "2026-10-09", "2026-10-12", "2026-10-13",
                                          "2026-10-14", "2026-10-15")}
        self.assertEqual([v["day"] for v in days.values()], [1, 2, 3, 4, 5, 6])
        self.assertEqual([v["active"] for v in days.values()], [True] * 5 + [False])

    def test_weekends_and_holidays_are_not_sessions(self):
        self.state(entry_start_date="2026-09-03", ultima_actualizacion="2026-09-04")
        # Thu 09-03, Fri 09-04, (weekend), Mon 09-07 Labor Day closed, Tue 09-08 -> day 3
        self.assertEqual(self.day("2026-09-08")["day"], 3)

    def test_older_state_falls_back_to_the_earliest_fill_then_run_ts(self):
        self.state(ultima_actualizacion="2026-10-09", dia_ciclo=2)
        (self.executions / f"fills_{QU}_{QU_STAMP}.json.bak").write_text(json.dumps(
            doc("sig-day1", "2026-10-08T15:00:00-05:00", fill("AVGO", 1, 0.1))), encoding="utf-8")
        (self.executions / f"fills_{QU}_{QU_STAMP}.json").write_text(json.dumps(
            doc("sig-day2", "2026-10-09T15:00:00-05:00", fill("AVGO", 1, 0.1))), encoding="utf-8")
        self.assertEqual(self.day("2026-10-12")["start_date"], "2026-10-08")
        self.assertEqual(self.day("2026-10-12")["day"], 3)
        for name in os.listdir(self.executions):
            os.remove(self.executions / name)
        self.assertEqual(self.day("2026-10-12")["start_date"], "2026-10-08")

    def test_fresh_portfolio_starts_today(self):
        info = self.day("2026-10-12")
        self.assertEqual((info["day"], info["start_date"], info["active"]), (1, "2026-10-12", True))

    def test_qu_is_on_day_3_today_and_day_4_tomorrow(self):
        self.state(ultima_actualizacion="2026-10-09", dia_ciclo=2)
        self.assertEqual(self.day("2026-10-12")["day"], 3)
        self.assertEqual(self.day("2026-10-13")["day"], 4)


class DrawdownPauseModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state_file = os.path.join(self.tmp.name, "rotation_state.json")
        holdings = {"KO": 0.4, "GLD": 0.3, "MRK": 0.3}
        series = {"KO": _ohlc(seed=1, last5=-0.09), "GLD": _ohlc(seed=2, last5=-0.04), "MRK": _ohlc(seed=3)}
        phase = {"day": 2, "start_date": "2026-10-08", "active": True, "last_day": 5}
        self.phase = phase
        self.universe = mock.Mock()
        patches = [
            mock.patch.dict(os.environ, {"ROTATION_STATE_FILE": self.state_file, "HEADLESS": "1",
                                         "FIGURES_DIR": self.tmp.name}),
            mock.patch.object(dr, "_PORTFOLIO_META", {"weights": holdings, "portfolio_source": "x",
                                                      "portfolio_run_ts": RUN_TS}),
            mock.patch.object(dr, "fetch_ohlc", side_effect=lambda t, days=0: series[t]),
            mock.patch.object(dr, "build_universe", self.universe),
            mock.patch.object(dr, "options_view", side_effect=AssertionError("no options in pause mode")),
            mock.patch.object(dr, "entry_phase_info", side_effect=lambda *a, **k: self.phase),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_entry_phase_marks_but_never_sells_or_rotates(self):
        with redirect_stdout(io.StringIO()):
            data, warns = dr.run()
        self.assertEqual(data["mode"], "pause")
        self.assertFalse(data["triggered"])
        self.assertEqual(data["rebalances"], [])
        self.assertEqual(data["pause"]["tickers"], ["KO"])
        self.assertEqual(data["pause"]["mode"], "pause")
        self.assertEqual(data["pause"]["entry_day"], 2)
        self.assertLess(data["pause"]["returns"]["KO"], -0.05)
        self.assertTrue(any("KO: paused" in w for w in warns))
        self.universe.assert_not_called()
        self.assertFalse(os.path.exists(self.state_file))

    def test_cooldown_does_not_hide_a_pause(self):
        pipeline_io.save_rotation_state(
            dict(pipeline_io.empty_rotation_state(),
                 triggers={"KO": {"date": "2026-10-09", "close": 1.0}}), {})
        with redirect_stdout(io.StringIO()):
            data, _ = dr.run()
        self.assertEqual(data["pause"]["tickers"], ["KO"])

    def test_from_day_6_the_rotation_runs_in_full(self):
        self.phase = {"day": 6, "start_date": "2026-10-08", "active": False, "last_day": 5}
        calm = {t: _ohlc(seed=i) for i, t in enumerate(("KO", "GLD", "MRK"))}
        with mock.patch.object(dr, "fetch_ohlc", side_effect=lambda t, days=0: calm[t]):
            with redirect_stdout(io.StringIO()):
                data, _ = dr.run()
        self.assertEqual(data["mode"], "full")
        self.assertIsNone(data["pause"])

    def test_mode_flag_overrides_the_phase(self):
        self.phase = {"day": 6, "start_date": "2026-10-08", "active": False, "last_day": 5}
        with redirect_stdout(io.StringIO()):
            data, _ = dr.run(mode="pause")
        self.assertEqual(data["pause"]["tickers"], ["KO"])
        self.assertEqual(dr.parse_args(["--mode", "full"]).mode, "full")
        self.assertEqual(dr.parse_args([]).mode, "auto")

    def test_pause_mark_reaches_entry_through_the_signal_file(self):
        with redirect_stdout(io.StringIO()):
            data, _ = dr.run()
        meta = {"weights": {}, "portfolio_source": "x", "portfolio_run_ts": RUN_TS,
                "portfolio_optimizer": OPT}
        exact = os.path.join(self.tmp.name, "signals")
        with mock.patch.dict(os.environ, {"SIGNALS_DIR_EXACT": exact}):
            pipeline_io.export_signals("drawdown_rotation", data, meta)
            mark = pipeline_io.load_pause_mark(meta, date.fromisoformat(data["cycle_date"]))
            self.assertEqual(mark["tickers"], ["KO"])
            self.assertEqual(pipeline_io.load_pause_mark(meta, "2026-01-02")["tickers"], [])
            other = dict(meta, portfolio_run_ts="2025-01-01T00:00:00-05:00")
            self.assertEqual(pipeline_io.load_pause_mark(other, data["cycle_date"])["tickers"], [])


class EntryUnitRuleTests(unittest.TestCase):
    def row(self, mode="opciones", pct=0.4):
        return {"ticker": "X", "modo_entrada": mode, "pct_entrada_sugerido": pct}

    def build(self, previo, dia, **kw):
        return est.construir_fila_estado(self.row(kw.pop("mode", "opciones"), kw.pop("pct", 0.4)),
                                         previo, 0.10, dia, 1, pd.DataFrame({"ticker": [], "fecha": []}), **kw)

    def test_paused_ticker_does_not_buy(self):
        fila = self.build(0.0, 2, pausado=True, pct=1.0)
        self.assertEqual((fila["accion"], fila["delta_sugerido_hoy_pct"]), ("PAUSA", 0.0))
        self.assertIn("PAUSA", fila["recomendacion"])

    def test_last_day_is_mandatory_for_everyone_paused_or_not(self):
        for kwargs in ({}, {"pausado": True}, {"con_pausas": True}):
            fila = self.build(0.3, 5, obligatorio=True, **kwargs)
            self.assertEqual(fila["accion"], "CIERRE: ENTRAR")
            self.assertEqual(fila["delta_sugerido_hoy_pct"], 70.0)
            self.assertEqual(fila["pct_invertido_final_pct"], 100.0)
            self.assertEqual(fila["cash_definitivo_pct"], 0.0)

    def test_mandatory_day_replaces_the_cash_decision_and_the_staggered_cap(self):
        # Without history the option-flow close would leave the rest in cash.
        self.assertEqual(self.build(0.3, 5)["accion"], "CIERRE: CASH")
        self.assertEqual(self.build(0.3, 5, obligatorio=True)["accion"], "CIERRE: ENTRAR")
        self.assertEqual(self.build(0.0, 5, mode="escalonado")["delta_sugerido_hoy_pct"], 20.0)
        full = self.build(0.0, 5, mode="escalonado", obligatorio=True)
        self.assertEqual(full["delta_sugerido_hoy_pct"], 100.0)

    def test_pending_amount_is_spread_over_the_remaining_days(self):
        # Paused on day 1 (0% invested). Day 2: at most 1/4 of what is left, not the whole score level.
        spread = self.build(0.0, 2, con_pausas=True, pct=1.0)
        self.assertEqual(spread["delta_sugerido_hoy_pct"], 25.0)
        plain = self.build(0.0, 2, pct=1.0)
        self.assertEqual(plain["delta_sugerido_hoy_pct"], 100.0)
        # The spread never asks for more than the conviction level.
        self.assertEqual(self.build(0.0, 2, con_pausas=True, pct=0.1)["delta_sugerido_hoy_pct"], 10.0)
        # Day 4 with 40% done: 60% / 2 days.
        self.assertEqual(self.build(0.4, 4, con_pausas=True, pct=1.0)["delta_sugerido_hoy_pct"], 30.0)
        # Staggered names catch up at the spread when it exceeds the fixed 20%.
        self.assertEqual(self.build(0.0, 3, mode="escalonado", con_pausas=True)["delta_sugerido_hoy_pct"], 33.3)

    def test_without_the_flags_the_old_behaviour_is_unchanged(self):
        self.assertEqual(self.build(0.0, 1, pct=0.4)["delta_sugerido_hoy_pct"], 40.0)
        self.assertEqual(self.build(0.0, 1, mode="escalonado")["accion"], "ESCALONADO")


def write_mark(case, day, tickers, returns=None):
    folder = case.signals / f"{OPT}_{STAMP}"
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "script": "drawdown_rotation", "portfolio_run_ts": RUN_TS,
               "data": {"pause": {"mode": "pause", "cycle_date": day, "entry_day": None,
                                  "tickers": tickers, "returns": returns or {t: -0.07 for t in tickers}}}}
    (folder / "drawdown_rotation.json").write_text(json.dumps(payload), encoding="utf-8")


def write_am(case, day, targets):
    folder = case.signals / f"{OPT}_{STAMP}"
    folder.mkdir(parents=True, exist_ok=True)
    rows = [{"ticker": t, "action": "SELL", "current_weight": 0.5, "target_weight": w,
             "delta_weight": w - 0.5, "tactical_action": "RECORTAR"} for t, w in targets.items()]
    rows.append({"ticker": "CASH", "action": "BUY", "target_weight": 0.1})
    payload = {"schema_version": 1, "script": "active_management", "run_ts": f"{day}T08:00:00-05:00",
               "portfolio_run_ts": RUN_TS, "data": {"rebalances": rows}}
    (folder / "active_management.json").write_text(json.dumps(payload), encoding="utf-8")


class CumulativeEntryCase(RotationEntryCase):
    """Executor that appends each tranche to the cumulative file (the new writer)."""

    def setUp(self):
        super().setUp()
        self.deals = itertools.count(1)
        ticks = itertools.count()
        base = datetime(2026, 10, 6, 9, 0, 0, tzinfo=pipeline_io.BOGOTA)
        patch = mock.patch.object(pipeline_io, "_now_bogota",
                                  side_effect=lambda: base + timedelta(seconds=next(ticks)))
        patch.start()
        self.addCleanup(patch.stop)

    def write_buys(self, signal, only=None):
        run_ts = signal["run_ts"]
        fills = []
        for e in signal["data"]["entries"]:
            if only is not None and e["ticker"] not in only:
                continue
            qty = round(e["tranche_weight"] * 1000, 6)
            fills.append({"ticker": e["ticker"], "action": "BUY", "filled_weight": e["tranche_weight"],
                          "filled_qty": qty, "price": 1.0, "status": "filled",
                          "deal_id": f"d{next(self.deals)}-{e['ticker']}"})
        pipeline_io.write_portfolio_fills(
            META, {"schema_version": 1, "signal_run_ts": run_ts, "executed_ts": run_ts, "fills": fills})

    def entry(self, signal, ticker):
        return {e["ticker"]: e for e in signal["data"]["entries"]}.get(ticker)


class EntryPhaseEntryTests(CumulativeEntryCase):
    def test_paused_ticker_is_not_bought_and_the_pause_is_remembered(self):
        write_mark(self, DAYS[0], ["JMT.LS"])
        signal = self.run_entry(DAYS[0])
        self.assertEqual([e["ticker"] for e in signal["data"]["entries"]], ["EDP.LS"])
        waiting = {w["ticker"]: w for w in signal["data"]["waiting"]}
        self.assertIn("PAUSA", waiting["JMT.LS"]["reason"])
        self.assertEqual(signal["data"]["paused"], ["JMT.LS"])
        self.assertEqual(signal["data"]["entry_phase"]["day"], 1)
        state = self.state()
        self.assertEqual(state["pausas_entrada"], {"JMT.LS": [DAYS[0]]})
        self.assertEqual(state["entry_start_date"], DAYS[0])

    def test_a_mark_of_another_day_is_ignored(self):
        write_mark(self, DAYS[0], ["JMT.LS"])
        signal = self.run_entry(DAYS[1])
        self.assertIn("JMT.LS", [e["ticker"] for e in signal["data"]["entries"]])

    def test_paused_tranche_accumulates_and_is_spread_over_the_remaining_days(self):
        write_mark(self, DAYS[0], ["JMT.LS"])
        first = self.run_entry(DAYS[0])
        self.write_buys(first)
        second = self.run_entry(DAYS[1])
        jmt, edp = self.entry(second, "JMT.LS"), self.entry(second, "EDP.LS")
        # Day 2, nothing bought yet: 1/4 of the target (EDP, never paused, buys its fixed 20%).
        self.assertAlmostEqual(jmt["tranche_weight"], round(0.25 * jmt["target_weight"], 6))
        self.assertAlmostEqual(edp["tranche_weight"], round(0.20 * edp["target_weight"], 6))

    def test_keeps_falling_means_paused_again(self):
        for day in DAYS[:3]:
            write_mark(self, day, ["JMT.LS"])
            signal = self.run_entry(day)
            self.write_buys(signal)
            self.assertNotIn("JMT.LS", [e["ticker"] for e in signal["data"]["entries"]])
        self.assertEqual(self.state()["pausas_entrada"]["JMT.LS"], DAYS[:3])

    def test_day_5_completes_100_percent_of_target_for_all_tickers(self):
        for day in DAYS[:4]:
            write_mark(self, day, ["JMT.LS"])
            self.write_buys(self.run_entry(day))
        write_mark(self, DAYS[4], ["JMT.LS"])
        last = self.run_entry(DAYS[4])
        self.assertEqual(last["data"]["cycle_day"], 5)
        jmt, edp = self.entry(last, "JMT.LS"), self.entry(last, "EDP.LS")
        self.assertEqual(jmt["signal"], "cycle_close")
        self.assertAlmostEqual(jmt["tranche_weight"], jmt["target_weight"])
        self.assertEqual(edp["signal"], "cycle_close")
        self.assertAlmostEqual(edp["tranche_weight"], round(0.2 * edp["target_weight"], 6))
        self.assertEqual(last["data"]["paused"], [])
        self.assertTrue(any("pause mark ignored" in w for w in last["warnings"]))
        self.assertEqual(last["data"]["entry_phase"]["day"], 5)

    def test_day_5_mandatory_even_when_a_day_was_skipped(self):
        # Only 3 runs (cycle day 3) but 5 sessions since day 1: the cycle still closes.
        for day in (DAYS[0], DAYS[1]):
            self.write_buys(self.run_entry(day))
        signal = self.run_entry(DAYS[4])
        self.assertTrue(all(e["signal"] == "cycle_close" for e in signal["data"]["entries"]))
        for e in signal["data"]["entries"]:
            self.assertEqual(e["reason"][:12], "CIERRE DIA 5")


class EntryUsesActiveManagementTargetsTests(CumulativeEntryCase):
    def finish_phase(self):
        for signal in self.full_cycle(DAYS[:5]):
            self.assertIn(signal["data"]["cycle_day"], range(1, 6))

    def test_targets_from_active_management_inside_the_phase_are_ignored(self):
        write_am(self, DAYS[0], {"JMT.LS": 0.25})
        signal = self.run_entry(DAYS[1])
        jmt = self.entry(signal, "JMT.LS")
        self.assertAlmostEqual(jmt["target_weight"], est.no_options_weight_cap(0.5))
        self.assertTrue(any("ignored" in w and "original optimizer targets" in w for w in signal["warnings"]))
        self.assertFalse(any("from active_management" in w for w in signal["warnings"]))

    def test_qu_day_4_buys_avgo_back_toward_its_original_target(self):
        start = date(2026, 10, 8)
        ran = "2026-10-12"
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / f"{QU}_{QU_STAMP}"
            folder.mkdir()
            rows = [{"ticker": "AVGO", "target_weight": 0.166}, {"ticker": "CASH", "target_weight": 0.0}]
            (folder / "active_management.json").write_text(json.dumps({
                "run_ts": f"{ran}T09:00:00-05:00", "portfolio_run_ts": QU_RUN_TS,
                "data": {"rebalances": rows}}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": tmp}):
                targets, info = pipeline_io.load_active_management_targets(QU_META, start)
                self.assertEqual((targets, info["status"], info["entry_day"]), ({}, "in_entry_phase", 3))
                day4 = pipeline_io.session_day(start, date(2026, 10, 13))
                self.assertEqual(day4, 4)
                self.assertLessEqual(day4, pipeline_io.ENTRY_PHASE_DAYS)
                # Replacement case: the same output, run after day 5, does count.
                (folder / "active_management.json").write_text(json.dumps({
                    "run_ts": "2026-10-19T09:00:00-05:00", "portfolio_run_ts": QU_RUN_TS,
                    "data": {"rebalances": rows}}), encoding="utf-8")
                targets, info = pipeline_io.load_active_management_targets(QU_META, start)
                self.assertEqual(targets, {"AVGO": 0.166})
                self.assertEqual(info["status"], "used")

    def test_output_of_another_portfolio_or_missing_gives_nothing(self):
        write_am(self, DAYS[8], {"JMT.LS": 0.25})
        other = dict(META, portfolio_run_ts="2025-01-01T00:00:00-05:00")
        folder = str(self.signals / f"{OPT}_{STAMP}")
        with mock.patch.dict(os.environ, {"SIGNALS_DIR_EXACT": folder}):
            self.assertEqual(pipeline_io.load_active_management_targets(other, DAYS[0])[1]["status"],
                             "other_portfolio")
        empty = Path(self.root / "empty")
        with mock.patch.dict(os.environ, {"SIGNALS_OUT_DIR": str(empty)}):
            self.assertEqual(pipeline_io.load_active_management_targets(META, DAYS[0])[1]["status"], "missing")

    def test_after_the_phase_a_lowered_target_stops_buying_that_name(self):
        self.finish_phase()
        write_am(self, DAYS[5], {"JMT.LS": 0.25})
        signal = self.run_entry(DAYS[5])
        self.assertTrue(any("JMT.LS: target 0.5000 -> 0.2500 from active_management" in w
                            for w in signal["warnings"]))
        self.assertIsNone(self.entry(signal, "JMT.LS"))
        self.assertNotIn("PAUSA", json.dumps(signal["data"]["waiting"]))

    def test_after_the_phase_a_raised_target_buys_the_missing_part(self):
        self.finish_phase()
        write_am(self, DAYS[5], {"JMT.LS": 0.8})
        signal = self.run_entry(DAYS[5])
        jmt = self.entry(signal, "JMT.LS")
        capped_new = est.no_options_weight_cap(0.8)
        invested = est.no_options_weight_cap(0.5)
        self.assertAlmostEqual(jmt["target_weight"], capped_new)
        # 62.5% of the new target is already in; the staggered 20% tranche goes on top.
        self.assertAlmostEqual(jmt["tranche_weight"], round(0.2 * capped_new, 6), places=5)
        self.assertAlmostEqual(invested / capped_new, 0.625)

    def test_without_active_management_output_the_optimizer_targets_stay(self):
        self.finish_phase()
        signal = self.run_entry(DAYS[5])
        self.assertFalse(any("from active_management" in w for w in signal["warnings"]))


class RunCyclePhaseTests(trc.CycleTestCase):
    MONDAY = "2026-10-12"
    ACTIVE = {"day": 3, "start_date": "2026-10-08", "active": True, "last_day": 5}

    def test_daily_runs_the_rotation_before_the_entry(self):
        steps = run_cycle.DAILY_STEPS
        self.assertLess(steps.index("drawdown_rotation"), steps.index("entry_signal_tool"))

    def test_weekly_active_management_is_skipped_in_the_entry_phase_even_on_monday(self):
        with mock.patch.object(run_cycle, "entry_phase", return_value=self.ACTIVE):
            result = self.invoke("--weekly", "--date", self.MONDAY)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, [])
        self.assertIn("not_due: entry_phase", result["stdout"])
        self.assertIn("day 3 of 5", result["stdout"])
        summary = self.summary(result)
        self.assertEqual(summary["status"], "not_due")
        self.assertIn("entry_phase", summary["not_due_reason"])
        self.assertFalse(os.path.exists(result["state"]))

    def test_force_does_not_bypass_the_entry_phase(self):
        with mock.patch.object(run_cycle, "entry_phase", return_value=self.ACTIVE):
            result = self.invoke("--weekly", "--force", "--date", self.MONDAY)
        self.assertEqual(self.commands, [])
        self.assertIn("entry_phase", result["stdout"])

    def test_dry_run_reports_the_skip(self):
        with mock.patch.object(run_cycle, "entry_phase", return_value=self.ACTIVE):
            result = self.invoke("--weekly", "--dry-run", "--date", self.MONDAY)
        self.assertEqual(result["code"], 0)
        self.assertIn("not_due: entry_phase", result["stdout"])

    def test_from_day_6_the_weekly_cycle_runs(self):
        past = {"day": 6, "start_date": "2026-10-05", "active": False, "last_day": 5}
        with mock.patch.object(run_cycle, "entry_phase", return_value=past):
            result = self.invoke("--weekly", "--date", self.MONDAY)
        self.assertEqual(result["code"], 0, result["stderr"])
        self.assertEqual(self.commands, ["active_management"])

    def test_daily_cycle_is_not_affected_by_the_phase(self):
        with mock.patch.object(run_cycle, "entry_phase", return_value=self.ACTIVE) as phase:
            result = self.invoke("--date", self.MONDAY)
        self.assertEqual(result["code"], 0, result["stderr"])
        phase.assert_not_called()
        self.assertIn("drawdown_rotation", self.commands)


class RunCycleEntryPhaseFunctionTests(unittest.TestCase):
    def test_counts_sessions_from_the_entry_state_of_the_portfolio(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp) / "entry_state.json"
            state.write_text(json.dumps({"entry_start_date": "2026-10-08",
                                         "ultima_actualizacion": "2026-10-09"}), encoding="utf-8")
            portfolio = {"path": "p.json", "optimizer": QU, "run_ts": QU_RUN_TS}
            with mock.patch.dict(os.environ, {"ENTRY_STATE_FILE": str(state)}):
                monday = run_cycle.entry_phase(portfolio, date(2026, 10, 12), tmp)
                tuesday = run_cycle.entry_phase(portfolio, date(2026, 10, 13), tmp)
                later = run_cycle.entry_phase(portfolio, date(2026, 10, 15), tmp)
        self.assertEqual((monday["day"], monday["active"]), (3, True))
        self.assertEqual((tuesday["day"], tuesday["active"]), (4, True))
        self.assertEqual((later["day"], later["active"]), (6, False))


if __name__ == "__main__":
    unittest.main()
