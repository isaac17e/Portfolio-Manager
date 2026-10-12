"""drawdown_rotation.py and universe.py. No network: prices, options and lists are fakes."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd

import pipeline_io
import universe


def _ohlc(n=300, drift=0.0005, vol=0.012, seed=0, last5=None, start=100.0):
    """Synthetic daily OHLC; ``last5`` forces the cumulative return of the last 5 sessions."""
    rng = np.random.default_rng(seed)
    rets = drift + vol * rng.standard_normal(n)
    close = start * np.exp(np.cumsum(rets))
    if last5 is not None:
        base = close[-6]
        steps = np.linspace(0, 1, 6)[1:]
        close[-5:] = base * (1 + last5 * steps)
    idx = pd.bdate_range(end=pd.Timestamp("2026-10-09"), periods=n)
    return pd.DataFrame({"high": close * 1.01, "low": close * 0.99, "close": close}, index=idx)


def _table(symbols, caps, names=None):
    return pd.DataFrame({
        "No.": range(1, len(symbols) + 1),
        "Symbol": symbols,
        "Company Name": names or [f"Co {s}" for s in symbols],
        "Market Cap": caps,
    })


class UniverseTests(unittest.TestCase):
    def test_parse_market_cap(self):
        self.assertEqual(universe.parse_market_cap("$3.5T"), 3.5e12)
        self.assertEqual(universe.parse_market_cap("812.3B"), 812.3e9)
        self.assertEqual(universe.parse_market_cap("950M"), 950e6)
        self.assertTrue(np.isnan(universe.parse_market_cap("n/a")))

    def test_sorted_by_cap_dedup_and_top_up(self):
        sp = _table(["AAA", "BBB", "CCC", "DDD", "EEE"], ["1T", "3T", "2T", "500B", "400B"])
        # NASDAQ shares BBB and AAA with the S&P list, and lists two classes of one company.
        nq = _table(["BBB", "GOOGL", "GOOG", "AAA", "NQ1", "NQ2", "NQ3"],
                    ["3T", "2.5T", "2.4T", "1T", "300B", "200B", "100B"],
                    names=["Co BBB", "Alphabet Inc.", "Alphabet Inc.", "Co AAA", "N1", "N2", "N3"])
        pages = {universe.SP500_URLS[0]: sp, universe.NASDAQ_URLS[0]: nq}
        out = universe.build_universe(3, 3, "indices", exclude=["CCC"], scraper=pages.get)
        # S&P by cap without the held CCC: BBB, AAA, DDD. NASDAQ fills 3 NEW names in
        # cap order: GOOGL (GOOG is the same company), NQ1, NQ2.
        self.assertEqual(out["tickers"], ["BBB", "AAA", "DDD", "GOOGL", "NQ1", "NQ2"])
        self.assertEqual(len(set(out["tickers"])), 6)
        self.assertEqual(out["shortfall"], {})

    def test_fallback_lists_and_shortfall(self):
        out = universe.build_universe(5, 5, "indices", scraper=lambda url: None)
        self.assertEqual(out["sources"], {"sp500": "fallback", "nasdaq": "fallback"})
        self.assertEqual(len(out["tickers"]), 10)
        self.assertEqual(len(set(out["tickers"])), 10)

    def test_custom_and_both(self):
        out = universe.build_universe(mode="custom", custom_tickers=["msft", "brk.b", "MSFT"],
                                      scraper=lambda url: None)
        self.assertEqual(out["tickers"], ["MSFT", "BRK-B"])
        both = universe.build_universe(2, 2, "both", custom_tickers=["ZZZ", "NVDA"],
                                       scraper=lambda url: None)
        self.assertEqual(both["tickers"][-1], "ZZZ")
        self.assertEqual(both["tickers"].count("NVDA"), 1)
        with self.assertRaises(ValueError):
            universe.build_universe(mode="all")


class RotationLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import drawdown_rotation
        cls.dr = drawdown_rotation

    def test_price_metrics_five_session_return(self):
        m = self.dr.price_metrics(_ohlc(last5=-0.08))
        self.assertAlmostEqual(m["ret_5d"], -0.08, places=9)
        self.assertTrue(np.isfinite(m["mom_12_1"]))
        self.assertLess(m["caida_sigmas"], 0)
        c = self.dr.cansancio_score(m)
        self.assertTrue(0 <= c["total"] <= 100)

    def test_trigger_threshold_and_cooldown(self):
        ohlc = _ohlc(last5=-0.06)
        m = self.dr.price_metrics(ohlc)
        self.assertTrue(self.dr.should_trigger("X", m, ohlc.index, {})[0])
        self.assertFalse(self.dr.should_trigger("X", self.dr.price_metrics(_ohlc(last5=-0.04)),
                                                ohlc.index, {})[0])
        # Triggered 2 sessions ago at almost the same price: cooldown.
        previo = {"X": {"date": str(ohlc.index[-3].date()), "close": m["precio"] * 1.01}}
        dispara, motivo = self.dr.should_trigger("X", m, ohlc.index, previo)
        self.assertFalse(dispara)
        self.assertIn("enfriamiento", motivo)
        # Another 5% below the previous trigger close: fires again inside the cooldown.
        previo = {"X": {"date": str(ohlc.index[-3].date()), "close": m["precio"] / 0.94}}
        self.assertTrue(self.dr.should_trigger("X", m, ohlc.index, previo)[0])
        # A trigger 5+ sessions ago belongs to an old window.
        previo = {"X": {"date": str(ohlc.index[-8].date()), "close": m["precio"]}}
        self.assertTrue(self.dr.should_trigger("X", m, ohlc.index, previo)[0])

    def test_decide_action(self):
        self.assertEqual(self.dr.decide_action(10), ("MANTENER", 0.0))
        self.assertEqual(self.dr.decide_action(85), ("LIQUIDAR", 1.0))
        accion, recorte = self.dr.decide_action(55)
        self.assertEqual(accion, "RECORTAR")
        self.assertAlmostEqual(recorte, 0.5)
        self.assertAlmostEqual(self.dr.decide_action(40)[1], 0.25)

    def test_options_scores(self):
        self.assertEqual(self.dr.options_risk_score(100), 0.0)
        self.assertEqual(self.dr.options_risk_score(-100), 100.0)
        self.assertEqual(self.dr.options_risk_score(np.nan), 50.0)
        self.assertEqual(self.dr.options_favor_score(np.nan), 50.0)

    def test_screen_discards_falling_candidates(self):
        rows = []
        for i, (drift, last5) in enumerate([(0.002, None), (0.0, None), (0.003, -0.07)]):
            m = self.dr.price_metrics(_ohlc(drift=drift, seed=i, last5=last5))
            rows.append({"ticker": f"C{i}", "origin": "sp500", **m, "tactical_score": 20.0})
        ranked = self.dr.screen_candidates(rows)
        self.assertTrue(ranked.loc[ranked["ticker"] == "C2", "descartado"].iloc[0])
        self.assertEqual(ranked.iloc[0]["ticker"], "C0")

    def test_choose_combination_prefers_best_sharpe_and_splits_equally(self):
        names = ["H1", "A", "B", "C"]
        base = np.array([0.5, 0.0, 0.0, 0.0])
        mu = np.array([0.02, 0.10, 0.02, -0.05])
        sig = np.array([0.2, 0.2, 0.2, 0.2])
        cov = np.diag(sig ** 2)
        best, evaluated = self.dr.choose_combination(names, base, mu, cov, 0.5, ["A", "B", "C"])
        self.assertEqual(best["tickers"], ["A"])
        self.assertEqual(len(evaluated), 3 + 3 + 1)
        self.assertTrue(all(len(e["tickers"]) <= 3 for e in evaluated))

    def test_state_overrides_feed_target_weights(self):
        state = pipeline_io.empty_rotation_state()
        triggers = [{"ticker": "KO", "precio": 60.0, "ret_5d": -0.07, "accion": "RECORTAR",
                     "recorte_pct": 0.5, "peso_actual": 0.1, "peso_nuevo": 0.05, "peso_liberado": 0.05,
                     "diagnostico": {"total": 55.0}}]
        state = self.dr.update_state(state, triggers, ["NVDA", "AVGO"], 0.025, "2026-10-09")
        weights, notes = pipeline_io.apply_rotation_overrides({"KO": 0.1, "GLD": 0.9}, state)
        self.assertEqual(weights, {"KO": 0.05, "GLD": 0.9, "NVDA": 0.025, "AVGO": 0.025})
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertEqual(len(notes), 3)
        liquidated = dict(state, target_overrides={"KO": 0.0})
        self.assertNotIn("KO", pipeline_io.apply_rotation_overrides({"KO": 0.1}, liquidated)[0])

    def test_rebalances_freed_equals_bought(self):
        triggers = [{"ticker": "KO", "recorte_pct": 1.0, "peso_actual": 0.06, "peso_nuevo": 0.0,
                     "motivo": "-8%", "accion": "LIQUIDAR", "diagnostico": {"total": 80.0}}]
        rows = self.dr.build_rebalances(triggers, ["A", "B", "C"], 0.02)
        sold = -sum(r["delta_weight"] for r in rows if r["action"] == "SELL")
        bought = sum(r["delta_weight"] for r in rows if r["action"] == "BUY")
        self.assertAlmostEqual(sold, bought)
        self.assertEqual([r["ticker"] for r in rows if r["action"] == "BUY"], ["A", "B", "C"])


class RotationRunTests(unittest.TestCase):
    """Full run() with fake prices, options and universe."""

    def setUp(self):
        import drawdown_rotation
        self.dr = drawdown_rotation
        self.tmp = tempfile.TemporaryDirectory()
        self.state_file = os.path.join(self.tmp.name, "rotation_state.json")
        holdings = {"KO": 0.4, "GLD": 0.3, "MRK": 0.3}
        series = {"KO": _ohlc(seed=1, last5=-0.09), "GLD": _ohlc(seed=2), "MRK": _ohlc(seed=3)}
        cands = [f"C{i}" for i in range(12)]
        for i, c in enumerate(cands):
            series[c] = _ohlc(seed=10 + i, drift=0.0002 * i)
        tactical = {"KO": -70.0, **{c: (i * 8.0 - 40) for i, c in enumerate(cands)}}

        def fake_view(ticker, horizon_days):
            score = tactical.get(ticker, 0.0)
            return {"tactical_score": score, "iv_atm": 0.25, "expected_move_pct": 0.05,
                    "rationale": "fake", "status": "OK"}

        info = {"tickers": cands, "rows": [{"ticker": c, "origin": "sp500"} for c in cands],
                "sources": {"sp500": "fake"}, "shortfall": {}}
        self.patches = [
            mock.patch.dict(os.environ, {"ROTATION_STATE_FILE": self.state_file, "HEADLESS": "1",
                                         "FIGURES_DIR": self.tmp.name}),
            mock.patch.object(self.dr, "_PORTFOLIO_META", {"weights": holdings,
                                                            "portfolio_source": "hardcoded_fallback"}),
            mock.patch.object(self.dr, "fetch_ohlc", side_effect=lambda t, days=0: series[t]),
            mock.patch.object(self.dr, "options_view", side_effect=fake_view),
            mock.patch.object(self.dr, "build_universe", return_value=info),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.tmp.cleanup()

    def test_trigger_liquidates_and_rotates_into_at_most_three(self):
        data, _ = self.dr.run(mode="full")
        self.assertTrue(data["triggered"])
        trig = data["triggers"][0]
        self.assertEqual(trig["ticker"], "KO")
        self.assertIn(trig["action"], ("RECORTAR", "LIQUIDAR"))
        self.assertEqual(len(data["top"]), 10)
        sel = data["selection"]
        self.assertTrue(1 <= len(sel["tickers"]) <= 3)
        self.assertAlmostEqual(sel["weight_each"] * len(sel["tickers"]), trig["freed_weight"])
        self.assertTrue(set(sel["tickers"]) <= {r["ticker"] for r in data["top"]})
        # State written: KO reduced, the new names carry the freed weight.
        state = json.loads(open(self.state_file, encoding="utf-8").read())
        weights, _ = pipeline_io.apply_rotation_overrides({"KO": 0.4, "GLD": 0.3, "MRK": 0.3}, state)
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights.get("KO", 0.0), trig["target_weight"])
        # Same drop the next run: cooldown, no second rotation.
        data2, _ = self.dr.run(mode="full")
        self.assertFalse(data2["triggered"])

    def test_dry_run_keeps_state(self):
        data, _ = self.dr.run(dry_run=True, mode="full")
        self.assertTrue(data["triggered"])
        self.assertTrue(data["dry_run"])
        self.assertFalse(os.path.exists(self.state_file))

    def test_no_drop_means_no_universe_and_no_rotation(self):
        calm = {t: _ohlc(seed=i) for i, t in enumerate(("KO", "GLD", "MRK"))}
        with mock.patch.object(self.dr, "fetch_ohlc", side_effect=lambda t, days=0: calm[t]):
            data, _ = self.dr.run(mode="full")
        self.assertFalse(data["triggered"])
        self.assertEqual(data["rebalances"], [])
        self.dr.build_universe.assert_not_called()
        self.assertFalse(os.path.exists(self.state_file))


class EntryReadsRotationTests(unittest.TestCase):
    def test_entry_targets_include_rotation(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_file = os.path.join(tmp, "rotation.json")
            state = pipeline_io.empty_rotation_state()
            state["target_overrides"] = {"KO": 0.0, "NVDA": 0.0578}
            with open(state_file, "w", encoding="utf-8") as handle:
                json.dump(state, handle)
            env = dict(os.environ, ROTATION_STATE_FILE=state_file,
                       PORTFOLIO_FILE=os.path.join(tmp, "missing.json"))
            code = ("import entry_signal_tool as e, json; "
                    "print(json.dumps({'t': e.TICKERS, 'w': e.PESOS_OBJETIVO['NVDA']}))")
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                 env=env, cwd=os.getcwd(), timeout=120)
            self.assertEqual(out.returncode, 0, out.stderr)
            payload = json.loads(out.stdout.strip().splitlines()[-1])
            self.assertIn("NVDA", payload["t"])
            self.assertNotIn("KO", payload["t"])
            self.assertAlmostEqual(payload["w"], 0.0578)


if __name__ == "__main__":
    unittest.main()
