"""Configuration and safe execution guardrails for Solana Block Ordering Analyzer.
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class AnalyzerConfig:
    # RPC endpoints: default to public mainnet, overrideable via env
    rpc_url: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    commitment: str = "confirmed"
    
    # Execution modes: Safety first!
    dry_run: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")
    
    # Financial guardrails: Hard spending cap for live transactions (<= 0.05 SOL)
    max_spend_sol: float = float(os.getenv("MAX_SPEND_SOL", "0.05"))
    current_spend_sol: float = 0.0
    
    # Network & timeout settings
    timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT", "15"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Historical / Target slot settings
    post_alpenglow_epoch: int = 680 # Measurements strictly post-Alpenglow (after Oct 21, 2026)
    
    # Target client versions to sample (minimum 3 distinct versions required)
    target_client_families = ["Agave", "Jito-Solana", "Frankendancer", "Firedancer"]

DEFAULT_CONFIG = AnalyzerConfig()
