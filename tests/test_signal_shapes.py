"""Shape checks for the six signal payloads. Loads only the builder functions."""

import ast
import json
import unittest
from typing import Any, Dict

import numpy as np
import pandas as pd

import pipeline_io


def _load_function(path, name, namespace):
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            module = ast.Module(body=[node], type_ignores=[])
            exec(compile(module, path, "exec"), namespace)
            return namespace[name]
    raise AssertionError(f"{name} not found in {path}")


class SignalShapeTests(unittest.TestCase):
    def test_entry_signal_orders_buys_and_lists_waiting(self):
        build = _load_function(
            "entry_signal_tool.py",
            "construir_senal_entrada",
            {"pd": pd, "UMBRAL_ALTO": 75, "UMBRAL_MEDIO": 40},
        )
        resumen = pd.DataFrame([
            {
                "ticker": "GLD", "score_conviccion": 80.0, "peso_objetivo_pct": 12.0,
                "delta_sugerido_hoy_pct": 100.0, "accion": "SUMAR",
                "recomendacion": "COMPLETAR A 100%", "dia_ciclo": 2, "ciclo": 1,
            },
            {
                "ticker": "KO", "score_conviccion": 30.0, "peso_objetivo_pct": 5.78,
                "delta_sugerido_hoy_pct": 0.0, "accion": "MANTENER",
                "recomendacion": "MANTENER (ya en el nivel objetivo de hoy)",
                "dia_ciclo": 2, "ciclo": 1,
            },
            {
                "ticker": "T", "score_conviccion": 55.0, "peso_objetivo_pct": 10.31,
                "delta_sugerido_hoy_pct": 20.0, "accion": "SUMAR",
                "recomendacion": "SUMAR +20.0%", "dia_ciclo": 2, "ciclo": 1,
            },
        ])
        data = build(resumen)
        self.assertEqual([row["ticker"] for row in data["entries"]], ["GLD", "T"])
        self.assertEqual(data["entries"][0]["order"], 1)
        self.assertEqual(data["entries"][0]["action"], "BUY")
        self.assertEqual(data["entries"][0]["signal"], "high_conviction")
        self.assertEqual(data["entries"][0]["target_weight"], 0.12)
        self.assertEqual(data["entries"][0]["tranche_weight"], 0.12)
        self.assertEqual(data["entries"][1]["signal"], "medium_conviction")
        self.assertEqual(data["entries"][1]["tranche_weight"], round(0.2 * 0.1031, 6))
        self.assertEqual(data["waiting"], [{
            "ticker": "KO", "score": 30.0,
            "reason": "MANTENER (ya en el nivel objetivo de hoy)",
        }])
        self.assertEqual(data["cycle_day"], 2)
        self.assertEqual(data["cycle"], 1)
        self.assertIsNone(json.loads(json.dumps(pipeline_io.to_jsonable({
            "score": np.float64("nan"),
        })))["score"])

    def test_active_management_maps_weight_delta_to_buy_sell_hold(self):
        build = _load_function(
            "active_management.py",
            "_senal_gestion_activa",
            {"pd": pd},
        )
        tabla = pd.DataFrame([
            {"Ticker": "GLD", "Peso_Inicial": 0.18, "Nuevo_Peso": 0.22,
             "Accion": "AUMENTAR", "Racional": "gamma positivo"},
            {"Ticker": "SLV", "Peso_Inicial": 0.10, "Nuevo_Peso": 0.04,
             "Accion": "RECORTAR", "Racional": "recortar riesgo"},
            {"Ticker": "CASH", "Peso_Inicial": 0.0, "Nuevo_Peso": 0.06,
             "Accion": "RESERVA_TACTICA", "Racional": "Limite configurado: 30%"},
        ])
        data = build({
            "tabla_rebalanceo": tabla,
            "regimen_riesgo": {
                "estado": "OK",
                "alertas": ["REGIMEN DE ESTRES: vol alta"],
                "vol_portafolio": 14.2,
                "ratio_diversificacion": 1.3,
            },
        })
        self.assertEqual([row["action"] for row in data["rebalances"]], ["BUY", "SELL", "BUY"])
        self.assertEqual(data["rebalances"][0]["delta_weight"], 0.04)
        self.assertEqual(data["rebalances"][1]["tactical_action"], "RECORTAR")
        self.assertEqual(data["regime"], "stress")
        self.assertEqual(data["vol_portfolio"], 14.2)

    def test_risk_score_leverage_weighted_means(self):
        build = _load_function(
            "portfolio_risk_score_leverage.py",
            "_senal_riesgo",
            {"pd": pd, "risk_score_weights": {"hv": 0.30, "cvar": 0.30, "iv": 0.25, "gex_pcr": 0.15},
             "leverage_min": 2.0, "leverage_max": 5.0},
        )
        summary = pd.DataFrame([
            {"Activo": "GLD", "Peso_Inicial": 0.25, "Risk_Score": 80.0,
             "Apalancamiento": 2.0, "Exposicion_Efectiva": 0.5},
            {"Activo": "KO", "Peso_Inicial": 0.75, "Risk_Score": 20.0,
             "Apalancamiento": 4.0, "Exposicion_Efectiva": 3.0},
        ])
        detail = summary.copy()
        detail["HV"] = [0.2, 0.1]
        detail["CVaR"] = [0.03, 0.01]
        detail["IV"] = [0.18, np.nan]
        detail["gex_total"] = [-1e6, 2e6]
        detail["pcr_oi"] = [1.1, 0.7]
        data = build(
            {"summary": summary, "detail": detail},
            {"portfolio_iv": np.nan},
        )
        self.assertAlmostEqual(data["target_leverage"], 0.25 * 2 + 0.75 * 4)
        self.assertAlmostEqual(data["risk_score"], 0.25 * 80 + 0.75 * 20)
        self.assertEqual(data["components"]["by_ticker"][0]["ticker"], "GLD")
        self.assertIsNone(data["components"]["portfolio_iv"])
        self.assertIsNone(data["components"]["by_ticker"][1]["iv"])
        encoded = json.loads(json.dumps(pipeline_io.to_jsonable(data), allow_nan=False))
        self.assertIsNone(encoded["components"]["portfolio_iv"])


if __name__ == "__main__":
    unittest.main()
