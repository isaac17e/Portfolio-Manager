"""Real current weights (pipeline_io.current_holdings) and their use in gex / vix.
No network: prices are injected and the scripts' price lookups are patched."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pandas as pd

import pipeline_io
import portfolio_gex_field as gex
import portfolio_vix as vix

OPT = "quadratic_utility"
RUN_TS = "2026-10-08T12:12:53-05:00"
KEY = "quadratic_utility_20261008T121253"
META = {
    "weights": {"AVGO": 0.30, "AMZN": 0.40, "GLD": 0.30},
    "portfolio_source": "qu.json", "portfolio_run_ts": RUN_TS, "portfolio_optimizer": OPT,
}
TODAY = date(2026, 10, 14)  # Wednesday
FRESH_AS_OF = "2026-10-13T16:05:00-04:00"  # Tuesday: one session before today
STALE_AS_OF = "2026-10-12T16:05:00-04:00"  # Monday: two sessions before today
PRICES = {"AVGO": 400.0, "AMZN": 200.0, "MRK": 100.0, "GLD": 300.0}


def fill(ticker, qty, price=10.0, action="BUY", status="filled", **extra):
    return {"ticker": ticker, "action": action, "filled_qty": qty, "price": price,
            "status": status, **extra}


def buy_doc(*fills, signal_run_ts="sig-1"):
    return {"schema_version": 1, "signal_run_ts": signal_run_ts, "executed_ts": "t", "fills": list(fills)}


def sell_doc(*fills):
    return {"schema_version": 1, "script": "drawdown_rotation", "portfolio_optimizer": OPT,
            "portfolio_run_ts": RUN_TS, "fills": list(fills)}


def snapshot(as_of=FRESH_AS_OF, positions=None, **extra):
    doc = {"schema_version": 1, "portfolio_run_ts": RUN_TS, "portfolio_optimizer": OPT,
           "account_id": "ACC-1", "as_of": as_of, "source": "capital_positions",
           "positions": positions if positions is not None else [
               {"ticker": "AVGO", "qty": 10.0, "price": 400.0, "market_value": 4000.0},
               {"ticker": "MRK", "qty": 20.0, "price": 100.0, "market_value": 2000.0},
           ]}
    doc.update(extra)
    return doc


class HoldingsCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        patcher = mock.patch.dict(os.environ, {"EXECUTIONS_DIR": str(self.dir)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def put(self, name, payload):
        (self.dir / name).write_text(json.dumps(payload), encoding="utf-8")

    def put_avgo_story(self):
        """AVGO bought 18.09 then sold 3.44 (net 14.65); MRK bought as a new name."""
        self.put(f"fills_{KEY}.json", buy_doc(
            fill("AVGO", 10.0, deal_id="d1", fill_ts="2026-10-09T10:00:00-04:00"),
            fill("AVGO", 8.09, deal_id="d2", fill_ts="2026-10-12T10:00:00-04:00"),
            fill("AMZN", 20.0, deal_id="d3", fill_ts="2026-10-09T10:00:00-04:00"),
            fill("MRK", 5.0, deal_id="d4", fill_ts="2026-10-13T10:00:00-04:00"),
        ))
        self.put(f"sell_fills_{KEY}.json", sell_doc(
            fill("AVGO", 3.44, action="SELL", deal_id="s1", fill_ts="2026-10-13T11:00:00-04:00")))

    def current(self, **kwargs):
        kwargs.setdefault("today", TODAY)
        kwargs.setdefault("prices", PRICES)
        with redirect_stdout(io.StringIO()):
            return pipeline_io.current_holdings(META, str(self.dir), **kwargs)


class SnapshotTests(HoldingsCase):
    def test_fresh_snapshot_wins_over_fills(self):
        self.put_avgo_story()
        self.put(f"holdings_{KEY}.json", snapshot())
        result = self.current()
        self.assertEqual(result["weights_source"], "snapshot")
        self.assertEqual(result["as_of"], FRESH_AS_OF)
        self.assertEqual(sorted(result["weights"]), ["AVGO", "MRK"])
        self.assertAlmostEqual(result["weights"]["AVGO"], 4000 / 6000)
        self.assertAlmostEqual(result["weights"]["MRK"], 2000 / 6000)
        self.assertEqual(result["holdings"]["AVGO"]["qty"], 10.0)

    def test_stale_snapshot_is_ignored_with_a_warning(self):
        self.put(f"holdings_{KEY}.json", snapshot(as_of=STALE_AS_OF))
        self.put_avgo_story()
        result = self.current()
        self.assertEqual(result["weights_source"], "fills")
        self.assertTrue(any("ignored" in note and "sessions old" in note for note in result["warnings"]))

    def test_weekend_gap_counts_as_one_session(self):
        self.put(f"holdings_{KEY}.json", snapshot(as_of="2026-10-09T16:05:00-04:00"))  # Friday
        self.assertEqual(self.current(today=date(2026, 10, 12))["weights_source"], "snapshot")  # Monday
        self.assertEqual(self.current(today=date(2026, 10, 13))["weights_source"], "portfolio_file")

    def test_same_day_snapshot_is_fresh(self):
        self.put(f"holdings_{KEY}.json", snapshot(as_of="2026-10-14T09:45:00-04:00"))
        self.assertEqual(self.current()["weights_source"], "snapshot")

    def test_invalid_snapshots_are_ignored(self):
        cases = {
            "naive as_of": snapshot(as_of="2026-10-13T16:05:00"),
            "wrong schema": snapshot(schema_version=2),
            "other portfolio": snapshot(portfolio_run_ts="2026-10-01T09:00:00-05:00"),
            "other optimizer": snapshot(portfolio_optimizer="minimum_variance"),
            "no positions": snapshot(positions=[]),
            "future as_of": snapshot(as_of="2026-10-20T16:05:00-04:00"),
        }
        for label, payload in cases.items():
            with self.subTest(label):
                self.put(f"holdings_{KEY}.json", payload)
                self.assertEqual(self.current()["weights_source"], "portfolio_file")

    def test_snapshot_drops_zero_and_negative_qty_and_warns_on_negative(self):
        self.put(f"holdings_{KEY}.json", snapshot(positions=[
            {"ticker": "AVGO", "qty": 10.0, "price": 400.0, "market_value": 4000.0},
            {"ticker": "GLD", "qty": 0.0, "price": 300.0, "market_value": 0.0},
            {"ticker": "AMZN", "qty": -2.0, "price": 200.0, "market_value": -400.0},
        ]))
        result = self.current()
        self.assertEqual(list(result["weights"]), ["AVGO"])
        self.assertAlmostEqual(result["weights"]["AVGO"], 1.0)
        self.assertTrue(any("AMZN" in note and "negative" in note for note in result["warnings"]))
        self.assertFalse(any("GLD" in note for note in result["warnings"]))

    def test_snapshot_without_market_value_uses_qty_times_price(self):
        self.put(f"holdings_{KEY}.json", snapshot(positions=[
            {"ticker": "AVGO", "qty": 10.0, "price": 400.0},
            {"ticker": "MRK", "qty": 10.0, "price": 100.0},
        ]))
        self.assertAlmostEqual(self.current()["weights"]["AVGO"], 0.8)


class FillsTests(HoldingsCase):
    def test_net_fills_trim_and_new_ticker(self):
        self.put_avgo_story()
        result = self.current()
        self.assertEqual(result["weights_source"], "fills")
        self.assertAlmostEqual(result["holdings"]["AVGO"]["qty"], 14.65)
        self.assertAlmostEqual(result["holdings"]["MRK"]["qty"], 5.0)
        self.assertIn("MRK", result["weights"])
        self.assertNotIn("GLD", result["weights"])
        values = {"AVGO": 14.65 * 400, "AMZN": 20 * 200, "MRK": 5 * 100}
        total = sum(values.values())
        for ticker, value in values.items():
            self.assertAlmostEqual(result["weights"][ticker], value / total)
        self.assertEqual(result["as_of"], "2026-10-13T11:00:00-04:00")

    def test_deal_id_may_be_a_string_or_a_list(self):
        self.put(f"fills_{KEY}.json", buy_doc(
            fill("AVGO", 10.0, deal_id="d1", fill_ts="2026-10-09T10:00:00-04:00"),
            fill("AMZN", 4.0, deal_id=["a1", "a2"], fill_ts="2026-10-09T10:00:00-04:00"),
            fill("AMZN", 6.0, deal_id=["a3"], fill_ts="2026-10-10T10:00:00-04:00"),
        ))
        self.put(f"sell_fills_{KEY}.json", sell_doc(
            fill("AVGO", 2.0, action="SELL", deal_id=["s1", "s2"], fill_ts="2026-10-12T10:00:00-04:00"),
            fill("AMZN", 1.0, action="SELL", deal_id="s3", fill_ts="2026-10-12T10:00:00-04:00"),
        ))
        result = self.current()
        self.assertAlmostEqual(result["holdings"]["AVGO"]["qty"], 8.0)
        self.assertAlmostEqual(result["holdings"]["AMZN"]["qty"], 9.0)

    def test_same_fill_in_two_files_counts_once(self):
        shared = fill("AVGO", 10.0, deal_id="d1", fill_ts="2026-10-09T10:00:00-04:00")
        self.put(f"fills_{KEY}.json", buy_doc(shared))
        self.put(f"fills_{KEY}.json.bak", buy_doc(dict(shared)))
        self.assertAlmostEqual(self.current()["holdings"]["AVGO"]["qty"], 10.0)

    def test_bak_files_are_read_only_when_backups_are_included(self):
        self.put(f"fills_{KEY}.json", buy_doc(fill("AVGO", 4.0, deal_id="d2", fill_ts="2026-10-12T10:00:00-04:00")))
        self.put(f"fills_{KEY}.json.bak", buy_doc(fill("AVGO", 6.0, deal_id="d1", fill_ts="2026-10-09T10:00:00-04:00")))
        self.assertAlmostEqual(self.current()["holdings"]["AVGO"]["qty"], 10.0)
        self.assertAlmostEqual(self.current(include_backups=False)["holdings"]["AVGO"]["qty"], 4.0)

    def test_sell_bak_files_are_never_read(self):
        self.put(f"fills_{KEY}.json", buy_doc(fill("AVGO", 10.0, deal_id="d1")))
        self.put(f"sell_fills_{KEY}.json.bak", sell_doc(fill("AVGO", 5.0, action="SELL", deal_id="s1")))
        self.assertAlmostEqual(self.current()["holdings"]["AVGO"]["qty"], 10.0)

    def test_only_filled_status_counts(self):
        self.put(f"fills_{KEY}.json", buy_doc(
            fill("AVGO", 10.0, deal_id="d1"),
            fill("AMZN", 7.0, status="rejected", deal_id="d2"),
            fill("MRK", 3.0, status="pending", deal_id="d3"),
        ))
        self.assertEqual(list(self.current()["weights"]), ["AVGO"])

    def test_fully_sold_and_oversold_tickers_are_dropped(self):
        self.put(f"fills_{KEY}.json", buy_doc(
            fill("AVGO", 10.0, deal_id="d1"), fill("AMZN", 5.0, deal_id="d2"), fill("MRK", 2.0, deal_id="d3")))
        self.put(f"sell_fills_{KEY}.json", sell_doc(
            fill("AVGO", 10.0, action="SELL", deal_id="s1"),
            fill("AMZN", 9.0, action="SELL", deal_id="s2"),
            fill("GLD", 1.0, action="SELL", deal_id="s3"),
        ))
        result = self.current()
        self.assertEqual(list(result["weights"]), ["MRK"])
        notes = " ".join(result["warnings"])
        self.assertIn("AMZN", notes)
        self.assertIn("GLD", notes)
        self.assertNotIn("AVGO", notes)

    def test_price_priority_and_last_fill_price_is_flagged(self):
        self.put(f"fills_{KEY}.json", buy_doc(
            fill("AVGO", 10.0, price=350.0, deal_id="d1", fill_ts="2026-10-09T10:00:00-04:00"),
            fill("AVGO", 5.0, price=380.0, deal_id="d2", fill_ts="2026-10-12T10:00:00-04:00"),
            fill("AMZN", 10.0, price=190.0, deal_id="d3", fill_ts="2026-10-09T10:00:00-04:00"),
            fill("MRK", 10.0, price=90.0, deal_id="d4", fill_ts="2026-10-09T10:00:00-04:00"),
        ))
        result = self.current(prices={"AMZN": 200.0}, price_fn=lambda t: {"MRK": 100.0}.get(t))
        holdings = result["holdings"]
        self.assertEqual(holdings["AMZN"]["price"], 200.0)
        self.assertEqual(holdings["MRK"]["price"], 100.0)
        self.assertEqual(holdings["AVGO"]["price"], 380.0)
        self.assertEqual(holdings["AVGO"]["price_source"], "last_fill")
        self.assertEqual(result["price_fallback_tickers"], ["AVGO"])
        self.assertTrue(any("last fill price" in note for note in result["warnings"]))

    def test_price_fn_errors_fall_back_to_last_fill_price(self):
        self.put(f"fills_{KEY}.json", buy_doc(fill("AVGO", 10.0, price=350.0, deal_id="d1")))

        def boom(_ticker):
            raise RuntimeError("offline")

        result = self.current(prices=None, price_fn=boom)
        self.assertEqual(result["weights_source"], "fills")
        self.assertEqual(result["holdings"]["AVGO"]["price"], 350.0)
        self.assertEqual(result["price_fallback_tickers"], ["AVGO"])


class FallbackChainTests(HoldingsCase):
    def test_snapshot_then_fills_then_portfolio_file(self):
        self.put_avgo_story()
        self.put(f"holdings_{KEY}.json", snapshot())
        self.assertEqual(self.current()["weights_source"], "snapshot")
        self.put(f"holdings_{KEY}.json", snapshot(as_of=STALE_AS_OF))
        self.assertEqual(self.current()["weights_source"], "fills")
        for path in self.dir.glob("*fills_*"):
            path.unlink()
        result = self.current()
        self.assertEqual(result["weights_source"], "portfolio_file")
        self.assertEqual(result["weights"], META["weights"])
        self.assertEqual(result["as_of"], RUN_TS)

    def test_fills_that_cannot_be_priced_fall_through(self):
        self.put(f"fills_{KEY}.json", buy_doc({"ticker": "AVGO", "action": "BUY", "filled_qty": 5.0,
                                               "status": "filled", "deal_id": "d1"}))
        result = self.current(prices=None)
        self.assertEqual(result["weights_source"], "portfolio_file")

    def test_unreadable_files_do_not_raise(self):
        (self.dir / f"holdings_{KEY}.json").write_text("{not json", encoding="utf-8")
        (self.dir / f"fills_{KEY}.json").write_text("[]", encoding="utf-8")
        self.assertEqual(self.current()["weights_source"], "portfolio_file")

    def test_missing_directory_and_missing_portfolio_key(self):
        with redirect_stdout(io.StringIO()):
            missing = pipeline_io.current_holdings(META, str(self.dir / "nope"), today=TODAY)
            hardcoded = pipeline_io.current_holdings({"weights": {"X": 1.0}}, str(self.dir), today=TODAY)
        self.assertEqual(missing["weights_source"], "portfolio_file")
        self.assertEqual(hardcoded["weights"], {"X": 1.0})
        self.assertIsNone(hardcoded["as_of"])

    def test_default_directory_comes_from_the_environment(self):
        self.put_avgo_story()
        with redirect_stdout(io.StringIO()):
            result = pipeline_io.current_holdings(META, prices=PRICES, today=TODAY)
        self.assertEqual(result["weights_source"], "fills")

    def test_other_portfolios_files_are_ignored(self):
        self.put("fills_minimum_variance_20261008T112902.json", buy_doc(fill("GLD", 9.0, deal_id="x")))
        self.put("holdings_minimum_variance_20261008T112902.json", snapshot())
        self.assertEqual(self.current()["weights_source"], "portfolio_file")


class WeightsTests(HoldingsCase):
    def test_weights_sum_to_one_over_invested_positions(self):
        self.put_avgo_story()
        weights = self.current()["weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertTrue(all(w > 0 for w in weights.values()))

    def test_snapshot_weights_ignore_cash(self):
        self.put(f"holdings_{KEY}.json", snapshot(cash=50_000.0, pending_cash=10_000.0))
        weights = self.current()["weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertNotIn("CASH", weights)

    def test_load_portfolio_holdings_keeps_its_old_shape(self):
        self.put_avgo_story()
        row = pipeline_io.load_portfolio_holdings(META)["AVGO"]
        self.assertAlmostEqual(row["net_qty"], 14.65)
        self.assertAlmostEqual(row["bought_qty"], 18.09)


class ScriptCase(HoldingsCase):
    def setUp(self):
        super().setUp()
        self.put_avgo_story()
        today = mock.patch.dict(os.environ, {"CYCLE_DATE": TODAY.isoformat()})
        today.start()
        self.addCleanup(today.stop)


class GexWeightsTests(ScriptCase):
    def _use_real_weights(self):
        stack = [
            mock.patch.object(gex, "_PORTFOLIO_META", META),
            mock.patch.object(gex, "PORTFOLIO_HOLDINGS", dict(META["weights"])),
            mock.patch.object(gex, "_TENENCIAS", {"weights_source": "portfolio_file", "as_of": RUN_TS,
                                                  "price_fallback_tickers": []}),
            mock.patch.object(gex, "get_current_price", side_effect=lambda t: PRICES[t]),
        ]
        for patcher in stack:
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_gex_uses_real_tickers_and_weights(self):
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            weights = gex.actualizar_tenencias()
        self.assertEqual(sorted(weights), ["AMZN", "AVGO", "MRK"])
        self.assertAlmostEqual(weights["AVGO"], 14.65 * 400 / (14.65 * 400 + 4000 + 500))
        self.assertAlmostEqual(sum(weights.values()), 1.0)
        signal = gex._senal_gex({})
        self.assertEqual(signal["weights_source"], "fills")
        self.assertEqual(signal["as_of"], "2026-10-13T11:00:00-04:00")
        self.assertEqual(signal["holdings"], [])
        self.assertEqual(gex._meta_senal()["weights"], weights)

    def test_gex_signal_carries_weights_and_keeps_old_keys(self):
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            gex.actualizar_tenencias()
        data = {"AVGO": {"weight_normalized": 0.6, "price": 400.0, "metrics_structural": {}},
                "MRK": {"weight": 0.4, "price": 100.0, "metrics_structural": {}}}
        signal = gex._senal_gex({"portfolio_data": data})
        self.assertEqual(signal["weights_used"], {"AVGO": 0.6, "MRK": 0.4})
        for key in ("macro_y", "potential_z", "n_holdings", "holdings", "excluded"):
            self.assertIn(key, signal)
        self.assertEqual(signal["holdings"][0]["weight"], 0.6)

    def test_run_headless_exports_weights_source_and_real_weights(self):
        self._use_real_weights()
        with mock.patch.object(gex, "run_once", return_value=None), \
                mock.patch.object(gex, "export_signals") as export, \
                redirect_stdout(io.StringIO()):
            gex.run_headless()
        script, data, meta = export.call_args.args[:3]
        self.assertEqual(script, "portfolio_gex_field")
        self.assertEqual(data["weights_source"], "fills")
        self.assertIn("as_of", data)
        self.assertEqual(sorted(meta["weights"]), ["AMZN", "AVGO", "MRK"])
        self.assertNotIn("GLD", meta["weights"])

    def test_gex_without_fills_keeps_the_portfolio_file_weights(self):
        for path in self.dir.glob("*fills_*"):
            path.unlink()
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            weights = gex.actualizar_tenencias()
        self.assertEqual(weights, META["weights"])
        self.assertEqual(gex._senal_gex({})["weights_source"], "portfolio_file")


class VixWeightsTests(ScriptCase):
    def _use_real_weights(self):
        stack = [
            mock.patch.object(vix, "_PORTFOLIO_META", META),
            mock.patch.object(vix, "PORTFOLIO_HOLDINGS", dict(META["weights"])),
            mock.patch.object(vix, "_TENENCIAS", {"weights_source": "portfolio_file", "as_of": RUN_TS,
                                                  "price_fallback_tickers": []}),
            mock.patch.object(vix, "_spot_price", side_effect=lambda t: PRICES[t]),
        ]
        for patcher in stack:
            patcher.start()
            self.addCleanup(patcher.stop)

    def _parse(self, *argv):
        with mock.patch.object(sys, "argv", ["portfolio_vix.py", *argv]):
            return vix._parse_args()

    def _results(self, tickers, weights):
        frame = pd.DataFrame({"ticker": tickers, "peso": weights, "VIX_individual": [20.0] * len(tickers),
                              "sigma_30d": [0.2] * len(tickers), "MCR": [0.2] * len(tickers),
                              "CTR": [0.1] * len(tickers), "CTR_VIX_pts": [1.0] * len(tickers),
                              "CTR_%": [50.0] * len(tickers)}).set_index("ticker")
        return {"breakdown": frame, "metrics": {"sigma_portfolio_30d": 0.2}, "vix": 20.0,
                "source": "synthetic", "excluded": [], "horizon": None}

    def test_vix_cfg_and_signal_use_the_real_holdings(self):
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            vix.actualizar_tenencias()
        cfg = self._parse()
        self.assertEqual(sorted(cfg.tickers), ["AMZN", "AVGO", "MRK"])
        self.assertAlmostEqual(sum(cfg.weights), 1.0)
        self.assertEqual(dict(zip(cfg.tickers, cfg.weights))["AVGO"], vix.PORTFOLIO_HOLDINGS["AVGO"])
        signal = vix._senal_vix(self._results(cfg.tickers, cfg.weights), cfg)
        self.assertEqual(signal["weights_source"], "fills")
        self.assertEqual(signal["as_of"], "2026-10-13T11:00:00-04:00")
        self.assertEqual(sorted(signal["weights_used"]), ["AMZN", "AVGO", "MRK"])
        self.assertIn("vix_portfolio", signal)
        meta = vix._vix_portfolio_meta(cfg)
        self.assertEqual(sorted(meta["weights"]), ["AMZN", "AVGO", "MRK"])
        self.assertAlmostEqual(meta["weights"]["AVGO"], vix.PORTFOLIO_HOLDINGS["AVGO"])

    def test_cli_overrides_are_reported_as_cli(self):
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            vix.actualizar_tenencias()
        cfg = self._parse("--tickers", "SPY", "QQQ", "--weights", "0.6", "0.4")
        self.assertEqual(cfg.weights_source, "cli")
        signal = vix._senal_vix(self._results(["SPY", "QQQ"], [0.6, 0.4]), cfg)
        self.assertEqual(signal["weights_source"], "cli")
        self.assertIsNone(signal["as_of"])

    def test_signal_without_a_resolved_cfg_uses_the_module_state(self):
        self._use_real_weights()
        cfg = SimpleNamespace(vol_method="svi", corr_method="ewma", r=0.045, horizon_days=30.0)
        signal = vix._senal_vix(self._results(["GLD"], [1.0]), cfg)
        self.assertEqual(signal["weights_source"], "portfolio_file")
        self.assertEqual(signal["as_of"], RUN_TS)

    def test_vix_without_fills_keeps_the_portfolio_file_weights(self):
        for path in self.dir.glob("*fills_*"):
            path.unlink()
        self._use_real_weights()
        with redirect_stdout(io.StringIO()):
            weights = vix.actualizar_tenencias()
        self.assertEqual(weights, META["weights"])


if __name__ == "__main__":
    unittest.main()
