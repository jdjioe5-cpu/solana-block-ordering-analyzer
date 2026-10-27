"""Ordering Engine: Mathematical, statistical, and empirical rule derivation
for transaction ordering across different Solana validator forks.
"""
import math
from typing import Dict, List, Any

class OrderingEngine:
    @staticmethod
    def calculate_spearman_rank_correlation(x: List[float], y: List[float]) -> float:
        """Calculate Spearman rank correlation between two series."""
        n = len(x)
        if n < 3:
            return 0.0

        def get_ranks(seq):
            indexed = sorted(enumerate(seq), key=lambda item: item[1])
            ranks = [0.0] * n
            for rank, (original_idx, _) in enumerate(indexed):
                ranks[original_idx] = float(rank + 1)
            return ranks

        rx = get_ranks(x)
        ry = get_ranks(y)

        d_sq_sum = sum((rx[i] - ry[i]) ** 2 for i in range(n))
        return 1.0 - (6.0 * d_sq_sum) / (n * (n**2 - 1))

    @classmethod
    def evaluate_block_ordering(cls, parsed_block: Dict[str, Any]) -> Dict[str, Any]:
        """Derive ordering behavior, priority fee sensitivity, and client profile."""
        txs = parsed_block.get("transactions", [])
        n = len(txs)
        if n == 0:
            return {
                "sample_size": 0,
                "ordering_rule": "EMPTY_BLOCK",
                "priority_fee_correlation": 0.0,
                "jito_bundle_ratio": 0.0,
                "confidence": 0.0
            }

        indices = [float(tx["block_index"]) for tx in txs]
        # Invert priority fee so that higher fee = lower expected rank index (earlier in block)
        fees = [float(tx["priority_fee_micro_lamports"]) for tx in txs]
        jito_tips = [1 if tx["is_jito_tip"] else 0 for tx in txs]

        # Calculate rank correlation between block position and priority fee
        # Negative correlation means higher fee => earlier block position (expected under priority scheduler)
        correlation = cls.calculate_spearman_rank_correlation(indices, fees)

        # Check Jito bundle distribution (first 20% of block vs rest)
        first_quintile_limit = max(1, n // 5)
        jito_in_first_quintile = sum(jito_tips[:first_quintile_limit])
        total_jito = sum(jito_tips)
        jito_early_concentration = (jito_in_first_quintile / total_jito) if total_jito > 0 else 0.0

        # Classify the ordering rule
        rule = "STOCHASTIC_OR_FIFO"
        confidence = 0.5

        if total_jito > 0 and jito_early_concentration > 0.7:
            rule = "JITO_BUNDLE_PRIORITIZED"
            confidence = 0.88
        elif correlation < -0.35:
            rule = "FEE_WEIGHTED_PRIORITY_SCHEDULER"
            confidence = min(0.95, abs(correlation) * 1.5)
        elif abs(correlation) <= 0.15:
            rule = "PARALLEL_BANK_BATCHED_FIFO"
            confidence = 0.75
        else:
            rule = "HYBRID_FEE_CONGESTION_SCHEDULER"
            confidence = 0.65

        # Measure top-decile vs bottom-decile fee comparison
        sorted_by_index = txs
        decile_size = max(1, n // 10)
        early_fees = [t["priority_fee_micro_lamports"] for t in sorted_by_index[:decile_size]]
        late_fees = [t["priority_fee_micro_lamports"] for t in sorted_by_index[-decile_size:]]
        avg_early_fee = sum(early_fees) / len(early_fees)
        avg_late_fee = sum(late_fees) / len(late_fees)

        return {
            "sample_size": n,
            "ordering_rule": rule,
            "spearman_fee_correlation": round(correlation, 4),
            "total_jito_transactions": total_jito,
            "jito_early_concentration_pct": round(jito_early_concentration * 100, 2),
            "avg_early_priority_fee": round(avg_early_fee, 2),
            "avg_late_priority_fee": round(avg_late_fee, 2),
            "confidence_score": round(confidence, 2)
        }
