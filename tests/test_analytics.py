import unittest

import numpy as np
import pandas as pd

from aurelia_pension.analytics import (
    contribution_projection, historical_tail, metrics, peer_ranking,
    rebalance_portfolio, returns, walk_forward_var,
)


class AnalyticsTests(unittest.TestCase):
    def test_returns_hand_calculation(self):
        np.testing.assert_allclose(returns([100, 110, 99]), [.1, -.1])

    def test_drawdown_and_total_return(self):
        m = metrics([100, 120, 90, 108])
        self.assertAlmostEqual(m["max_drawdown"], -.25)
        self.assertAlmostEqual(m["total_return"], .08)

    def test_tail_worst_observation(self):
        # At N=20, 5% tail contains exactly one observation.
        risk = historical_tail([-.20, -.10] + [0.] * 18)
        self.assertAlmostEqual(risk["var95"], .1)
        self.assertAlmostEqual(risk["es95"], .2)

    def test_fractional_tail(self):
        risk = historical_tail([-.20, -.10] + [0.] * 28)
        self.assertAlmostEqual(risk["es95"], (.2 + .5 * .1) / 1.5)

    def test_no_loss_sample(self):
        self.assertEqual(historical_tail([.01, .02, .03]), {"var95": 0., "es95": 0.})

    def test_nav_validation(self):
        for nav in [[100, 0, 90], [100, float("nan"), 90], [100, float("inf"), 90]]:
            with self.subTest(nav=nav), self.assertRaises(ValueError):
                metrics(nav)

    def test_peer_ranks_never_cross_categories(self):
        f = peer_ranking(pd.DataFrame({"fund_id": ["A", "B", "C", "D"],
                                      "category": ["X", "X", "Y", "Y"],
                                      "total_return": [.8, .6, .1, .2]}))
        self.assertEqual(f.peer_rank.tolist(), [1, 2, 2, 1])

    def test_flat_benchmark_ratio_undefined(self):
        self.assertIsNone(metrics([1, 1, 1], [1, 1, 1])["information_ratio"])

    def test_benchmark_dates_must_align(self):
        dates = pd.bdate_range("2025-01-02", periods=3)
        nav = pd.Series([100, 101, 102], index=dates)
        benchmark = pd.Series([100, 100.5, 101], index=dates.shift(1, freq="B"))
        with self.assertRaisesRegex(ValueError, "share the same dates"):
            metrics(nav, benchmark)

    def test_contributions_zero_growth(self):
        final = contribution_projection(5000, 2, 0, 0)[-1]
        self.assertEqual(final["balance"], 120000)
        self.assertEqual(final["paid"], 120000)

    def test_contributions_annual_escalation(self):
        final = contribution_projection(100, 2, 0, 0, .1)[-1]
        self.assertAlmostEqual(final["paid"], 2520)

    def test_beginning_of_month_annuity(self):
        g = 1.01
        actual = contribution_projection(100, 1, g**12 - 1, 0)[-1]["balance"]
        expected = 100 * g * (g**12 - 1) / (g - 1)
        self.assertAlmostEqual(actual, expected, places=8)

    def test_real_balance(self):
        final = contribution_projection(100, 2, .1, .2)[-1]
        self.assertAlmostEqual(final["real_balance"], final["balance"] / 1.2**2)

    def test_projection_invalid_values(self):
        for args in [(100, 1.5, .1, .1), (-1, 2, .1, .1), (100, 2, -1, .1),
                     (100, True, .1, .1), (100, 2, float("nan"), .1)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                contribution_projection(*args)

    def test_monthly_holdings_drift(self):
        frame = pd.DataFrame({"A": [100, 200, 200], "B": [100, 100, 200]},
                             index=pd.to_datetime(["2025-01-02", "2025-01-03", "2025-01-06"]))
        result = rebalance_portfolio(frame, {"A": .5, "B": .5}, 0)
        np.testing.assert_allclose(result.nav, [100, 150, 200])

    def test_monthly_rebalance_transaction_cost(self):
        frame = pd.DataFrame({"A": [100, 200, 200], "B": [100, 100, 100]},
                             index=pd.to_datetime(["2025-01-30", "2025-01-31", "2025-02-03"]))
        result = rebalance_portfolio(frame, {"A": .5, "B": .5}, 100)
        self.assertAlmostEqual(result.turnover.iloc[-1], 1 / 6)
        self.assertAlmostEqual(result.nav.iloc[-1], 149.75)

    def test_weights_not_silently_normalized(self):
        f = pd.DataFrame({"A": [1, 2, 3]}, index=pd.bdate_range("2025-01-01", periods=3))
        for weights in [{"A": .9}, {"A": -1}, {"B": 1}]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                rebalance_portfolio(f, weights)

    def test_no_lookahead_in_var(self):
        daily = np.r_[np.linspace(-.01, .01, 30), -.5, .001, .002]
        nav = np.r_[100, 100 * np.cumprod(1 + daily)]
        result = walk_forward_var(nav, 20)
        before_crash = result["forecasts"][10]
        self.assertLess(before_crash, .02)
        self.assertTrue(result["violations"][10])

    def test_var_prefix_invariance(self):
        daily = np.sin(np.arange(100)) * .01
        nav = np.r_[100, 100 * np.cumprod(1 + daily)]
        short = walk_forward_var(nav[:61], 20)
        full = walk_forward_var(nav, 20)
        np.testing.assert_allclose(short["forecasts"], full["forecasts"][:40])


if __name__ == "__main__":
    unittest.main()
