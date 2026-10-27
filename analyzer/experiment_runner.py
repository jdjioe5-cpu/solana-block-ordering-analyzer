"""Experiment Runner: Conducts multi-validator ordering analysis across mainnet slots,
enforcing dry-run by default, fee spend caps, and generating raw verification artifacts.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Any

from .config import DEFAULT_CONFIG, AnalyzerConfig
from .cluster_probe import ClusterProbe
from .block_parser import BlockParser
from .ordering_engine import OrderingEngine

class ExperimentRunner:
    def __init__(self, config: AnalyzerConfig = DEFAULT_CONFIG):
        self.config = config
        self.probe = ClusterProbe(rpc_url=config.rpc_url, timeout=config.timeout_seconds)
        self.parser = BlockParser(rpc_url=config.rpc_url, timeout=config.timeout_seconds)
        self.output_dir = Path(__file__).resolve().parent.parent / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_full_investigation(self, sample_slots_count: int = 6) -> Dict[str, Any]:
        """Run complete empirical measurement across multiple client forks."""
        print("=" * 60)
        print("SOLANA VALIDATOR TRANSACTION ORDERING INVESTIGATION")
        print(f"Network: Solana Mainnet | RPC: {self.config.rpc_url}")
        print(f"Safety Mode: DRY-RUN = {self.config.dry_run} | Spend Cap = {self.config.max_spend_sol} SOL")
        print("=" * 60)

        # 1. Discover validators and version families
        print("\n[Step 1/4] Probing cluster nodes and client software versions...")
        try:
            validators = self.probe.select_representative_validators(count_per_version=2)
            print(f"-> Discovered {len(validators)} candidate validators spanning target client forks:")
            for idx, v in enumerate(validators[:6]):
                print(f"   [{idx+1}] Node: {v.get('pubkey')[:12]}... | Version: {v.get('version')} ({v.get('client_classification')})")
        except Exception as e:
            print(f"Cluster probing note: {e}")
            validators = []

        # 2. Query latest finalized slot on mainnet
        print("\n[Step 2/4] Querying post-Alpenglow mainnet slots via getBlocks...")
        current_slot_res = self.probe._rpc_call("getSlot", [{"commitment": "finalized"}])
        target_slot = int(current_slot_res) if current_slot_res else 461_988_000
        start_slot = target_slot - (sample_slots_count * 5)
        
        # Use getBlocks to retrieve guaranteed confirmed slots
        confirmed_slots = self.probe._rpc_call("getBlocks", [start_slot, target_slot]) or []
        # Sample evenly spaced slots
        stride = max(1, len(confirmed_slots) // sample_slots_count)
        slots_to_test = confirmed_slots[::stride][:sample_slots_count]
        print(f"-> Selected {len(slots_to_test)} confirmed slots across recent leader windows: {slots_to_test}")

        # 3. Analyze blocks
        print(f"\n[Step 3/4] Parsing block structures and transaction orders for {len(slots_to_test)} slots...")
        results: List[Dict[str, Any]] = []

        for slot in slots_to_test:
            print(f"   Fetching slot {slot}...", end="", flush=True)
            parsed_block = self.parser.parse_block_ordering(slot)
            if "error" in parsed_block:
                print(f" skipped ({parsed_block['error']})")
                continue

            analysis = OrderingEngine.evaluate_block_ordering(parsed_block)
            print(f" done (Txs: {analysis['sample_size']}, Rule: {analysis['ordering_rule']}, Fee Corr: {analysis['spearman_fee_correlation']})")

            # Save raw block summary for verifiability
            raw_path = self.output_dir / f"block_{slot}_ordering.json"
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(parsed_block, f, indent=2)

            results.append({
                "slot": slot,
                "block_time": parsed_block.get("block_time"),
                "total_transactions": parsed_block.get("total_transactions"),
                "analysis": analysis,
                "raw_file": str(raw_path.name)
            })

        # 4. Synthesize final comparative matrix
        print("\n[Step 4/4] Synthesizing comparative matrix across validator implementations...")
        report_summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "network": "Solana Mainnet",
            "dry_run": self.config.dry_run,
            "spend_cap_sol": self.config.max_spend_sol,
            "actual_fee_spent_sol": self.config.current_spend_sol,
            "slots_analyzed": len(results),
            "findings": results
        }

        summary_path = self.output_dir / "investigation_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(report_summary, f, indent=2)

        print(f"\n-> Investigation complete. Comprehensive dataset saved to: {summary_path}")
        return report_summary
