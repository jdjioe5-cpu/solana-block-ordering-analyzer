"""Command Line Interface for Solana Block Ordering Analyzer.
Reproducible with one command.
"""
import argparse
import json
import sys
from pathlib import Path

from .config import AnalyzerConfig
from .experiment_runner import ExperimentRunner

def main():
    parser = argparse.ArgumentParser(description="Solana Validator Transaction Ordering Investigation Suite")
    parser.add_argument("--run", action="store_true", help="Execute complete measurement suite")
    parser.add_argument("--slots", type=int, default=6, help="Number of slots/validators to evaluate (default: 6)")
    parser.add_argument("--rpc", type=str, default="https://api.mainnet-beta.solana.com", help="Solana Mainnet RPC endpoint")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Default dry-run mode (no fee expenditure)")
    parser.add_argument("--spend-cap", type=float, default=0.05, help="Hard spending limit in SOL (default: 0.05)")
    args = parser.parse_args()

    config = AnalyzerConfig(
        rpc_url=args.rpc,
        dry_run=args.dry_run,
        max_spend_sol=args.spend_cap
    )

    runner = ExperimentRunner(config=config)
    runner.run_full_investigation(sample_slots_count=args.slots)

if __name__ == "__main__":
    main()
