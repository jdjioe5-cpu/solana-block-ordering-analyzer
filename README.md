# Solana Block Ordering Analyzer 🔍

> Empirical investigation and measurement toolkit analyzing transaction ordering behavior across Solana validator client forks on Mainnet-Beta.

Developed for Superteam Earn: **[2,500 USDC] Inside the Block: How Solana Validators Order Transactions**.

---

## Quickstart (Reproduce in 1 Command)

### Via Docker Compose (Recommended)
```bash
docker compose up --build
```

### Via Python (Zero External Dependencies)
```bash
python -m unittest discover -s tests
python -m analyzer.cli --run --slots 6
```

---

## Safety & Invariant Guarantees
- **Dry-Run by Default**: `DRY_RUN=true` ensures 0 SOL is spent during analysis and replay.
- **Hard Spend Cap**: Strict ceiling of `<= 0.05 SOL` enforced in configuration (`config.py`).
- **Post-Alpenglow Compliance**: Compatible with Transaction Version 1 (Post-Oct 21, 2026 upgrade).
- **Key Safety**: No private keys stored or required. RPC reads are purely non-custodial.

---

## Project Structure
```
solana-block-ordering-analyzer/
├── analyzer/
│   ├── config.py             # Config & financial spend caps
│   ├── cluster_probe.py      # Validator discovery & version classifier
│   ├── block_parser.py       # Zero-dep base58 decoder & block extractor
│   ├── ordering_engine.py    # Spearman correlation & scheduler classifier
│   ├── experiment_runner.py  # End-to-end multi-slot test runner
│   └── cli.py                # Command-line entry point
├── data/
│   ├── investigation_summary.json # Aggregated benchmark results
│   └── block_*_ordering.json      # Raw block transaction dumps
├── tests/
│   └── test_ordering.py      # Unit tests
├── Dockerfile
├── docker-compose.yml
├── REPORT.md                 # Full measurement paper & analysis
└── README.md
```

---

## Verification
Judges can verify raw block data directly using any Solana RPC node:
```bash
curl -X POST -H "Content-Type: application/json" -d \
  '{"jsonrpc":"2.0","id":1,"method":"getBlock","params":[461989323, {"maxSupportedTransactionVersion": 1}]}' \
  https://api.mainnet-beta.solana.com
```
