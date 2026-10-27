import unittest
from analyzer.ordering_engine import OrderingEngine
from analyzer.config import AnalyzerConfig

class TestOrderingEngine(unittest.TestCase):
    def test_spearman_perfect_monotonic(self):
        # When indices [0, 1, 2] have decreasing fees [300, 200, 100], correlation should be 1.0 (with ranks)
        # Note: rank correlation between [0, 1, 2] and [300, 200, 100] is -1.0
        x = [0.0, 1.0, 2.0]
        y = [300.0, 200.0, 100.0]
        corr = OrderingEngine.calculate_spearman_rank_correlation(x, y)
        self.assertAlmostEqual(corr, -1.0, places=4)

    def test_jito_bundle_detection(self):
        mock_txs = [
            {"block_index": 0, "priority_fee_micro_lamports": 10000, "is_jito_tip": True},
            {"block_index": 1, "priority_fee_micro_lamports": 5000, "is_jito_tip": True},
            {"block_index": 2, "priority_fee_micro_lamports": 0, "is_jito_tip": False},
            {"block_index": 3, "priority_fee_micro_lamports": 0, "is_jito_tip": False},
            {"block_index": 4, "priority_fee_micro_lamports": 0, "is_jito_tip": False},
        ]
        res = OrderingEngine.evaluate_block_ordering({"transactions": mock_txs})
        self.assertEqual(res["total_jito_transactions"], 2)
        self.assertGreater(res["jito_early_concentration_pct"], 0.0)

    def test_safety_spend_cap_defaults(self):
        cfg = AnalyzerConfig()
        self.assertTrue(cfg.dry_run)
        self.assertLessEqual(cfg.max_spend_sol, 0.05)

if __name__ == "__main__":
    unittest.main()
