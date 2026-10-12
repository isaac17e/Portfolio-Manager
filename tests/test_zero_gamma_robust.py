"""zero_gamma_profile must never crash on near-zero / noisy GEX profiles
(brentq "f(a) and f(b) must have different signs"). No network."""

import unittest
from unittest import mock

import numpy as np

import gex_utils
from gex_utils import _grid_roots, _refine_bracket, zero_gamma_profile

S0 = 100.0
ONE_CONTRACT = ([100.0], [True], [10], [0.25], [0.1], S0, 0.05)


def _run_with_profile(fn, grid_fn=None):
    """zero_gamma_profile with ``_net_gex`` replaced by the scalar/vector function ``fn``.

    ``grid_fn`` (optional) is used for the vectorised grid call, so the grid
    values can disagree with the scalar re-evaluation inside brentq."""
    def fake(spots, contracts, r, scale):
        spots = np.asarray(spots, dtype=float)
        use = grid_fn if (grid_fn is not None and spots.size > 1) else fn
        return np.array([use(s) for s in spots], dtype=float)

    with mock.patch.object(gex_utils, "_net_gex", side_effect=fake):
        return zero_gamma_profile(*ONE_CONTRACT)


class RefineBracketTests(unittest.TestCase):
    def test_clean_sign_change_uses_brentq(self):
        self.assertAlmostEqual(_refine_bracket(lambda s: s - 101.5, 100.0, 103.0, 1e-9), 101.5)

    def test_reevaluation_without_sign_change_returns_none(self):
        self.assertIsNone(_refine_bracket(lambda s: 1e-12, 100.0, 101.0, 1e-9))
        self.assertIsNone(_refine_bracket(lambda s: -1e-12, 100.0, 101.0, 1e-9))

    def test_exact_zero_endpoint_is_the_root(self):
        self.assertEqual(_refine_bracket(lambda s: s - 100.0, 100.0, 101.0, 1e-9), 100.0)
        self.assertEqual(_refine_bracket(lambda s: s - 101.0, 100.0, 101.0, 1e-9), 101.0)

    def test_nonfinite_endpoint_returns_none(self):
        self.assertIsNone(_refine_bracket(lambda s: np.nan, 100.0, 101.0, 1e-9))

    def test_brentq_valueerror_falls_back_to_linear_interpolation(self):
        with mock.patch.object(gex_utils, "brentq", side_effect=ValueError("f(a) and f(b)")):
            root = _refine_bracket(lambda s: s - 100.25, 100.0, 101.0, 1e-9)
        self.assertAlmostEqual(root, 100.25)

    def test_function_error_returns_none(self):
        def boom(s):
            raise ValueError("bad")
        self.assertIsNone(_refine_bracket(boom, 100.0, 101.0, 1e-9))


class GridRootsTests(unittest.TestCase):
    def test_exact_zero_node_is_a_root(self):
        grid = np.array([1.0, 2.0, 3.0, 4.0])
        roots = _grid_roots(lambda s: s - 3.0, grid, grid - 3.0, 1e-9)
        self.assertEqual(roots, [3.0])

    def test_zero_run_is_one_root_at_its_midpoint(self):
        grid = np.arange(6, dtype=float)
        gex = np.array([-1.0, 0.0, 0.0, 0.0, 1.0, 2.0])
        self.assertEqual(_grid_roots(lambda s: 0.0, grid, gex, 1e-9), [2.0])

    def test_all_zero_or_nonfinite_has_no_roots(self):
        grid = np.arange(4, dtype=float)
        self.assertEqual(_grid_roots(lambda s: 0.0, grid, np.zeros(4), 1e-9), [])
        self.assertEqual(_grid_roots(lambda s: 0.0, grid, np.full(4, np.nan), 1e-9), [])

    def test_nan_nodes_are_skipped(self):
        grid = np.arange(5, dtype=float)
        gex = np.array([-1.0, np.nan, np.nan, 1.0, 2.0])
        roots = _grid_roots(lambda s: s - 1.5, grid, gex, 1e-9)
        self.assertEqual(len(roots), 1)

    def test_roots_are_ascending(self):
        grid = np.linspace(0, 10, 101)
        f = lambda s: np.sin(s)
        roots = _grid_roots(f, grid, np.sin(grid), 1e-9)
        self.assertEqual(roots, sorted(roots))
        self.assertEqual(len(roots), 4)  # pi, 2pi, 3pi and the node at 0 is exact zero
        np.testing.assert_allclose(roots, [0.0, np.pi, 2 * np.pi, 3 * np.pi], atol=1e-6)


class ZeroGammaProfileNeverCrashesTests(unittest.TestCase):
    def test_grid_sign_change_that_scalar_evaluation_does_not_confirm(self):
        # Grid says +/- around 100, the scalar sum is the same sign everywhere
        # (round-off): the old code let brentq raise ValueError.
        zg = _run_with_profile(lambda s: 1e-15, grid_fn=lambda s: 1e-15 if s >= 100 else -1e-15)
        self.assertEqual(zg["zero_gamma_status"], "no_crossing_in_grid")
        self.assertEqual(zg["zero_gamma_crossings"], [])

    def test_noisy_profile_around_zero_does_not_raise(self):
        rng = np.random.default_rng(7)
        noise = {}

        def noisy(s):
            return noise.setdefault(round(float(s), 9), float(rng.normal(scale=1e-9)))

        zg = _run_with_profile(noisy)
        self.assertIn(zg["zero_gamma_status"], ("ok", "no_crossing_in_grid"))
        for c in zg["zero_gamma_crossings"]:
            self.assertTrue(70.0 <= c <= 130.0)
        self.assertEqual(zg["zero_gamma_crossings"], sorted(zg["zero_gamma_crossings"]))

    def test_exact_zero_node_on_the_grid(self):
        zg = _run_with_profile(lambda s: float(s) - S0)
        self.assertEqual(zg["zero_gamma_status"], "ok")
        self.assertAlmostEqual(zg["zero_gamma_level"], S0, places=6)

    def test_near_zero_but_clean_crossing_is_found(self):
        zg = _run_with_profile(lambda s: (s - 101.234) * 1e-14)
        self.assertEqual(zg["zero_gamma_status"], "ok")
        self.assertAlmostEqual(zg["zero_gamma_level"], 101.234, places=4)

    def test_brentq_valueerror_is_absorbed(self):
        with mock.patch.object(gex_utils, "brentq", side_effect=ValueError("f(a) and f(b)")):
            zg = _run_with_profile(lambda s: float(s) - 98.7)
        self.assertEqual(zg["zero_gamma_status"], "ok")
        self.assertAlmostEqual(zg["zero_gamma_level"], 98.7, delta=0.01)

    def test_all_zero_profile(self):
        zg = _run_with_profile(lambda s: 0.0)
        self.assertEqual(zg["zero_gamma_status"], "no_crossing_in_grid")
        self.assertEqual(zg["grid_sign"], "all_zero")

    def test_real_chain_far_from_spot_is_near_zero_and_safe(self):
        # Deep OTM, short-dated contracts: GEX underflows to ~0 over most of the grid.
        zg = zero_gamma_profile([200.0, 50.0], [True, False], [1000, 1000], [0.05, 0.05],
                                [0.01, 0.01], S0, 0.05)
        self.assertIn(zg["zero_gamma_status"], ("ok", "no_crossing_in_grid"))


if __name__ == "__main__":
    unittest.main()
