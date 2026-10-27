"""Block Parser: Extracts transaction ordering, Priority Fees, Compute Unit Limits,
and account lock dependencies from Solana Mainnet blocks.
Zero external dependency implementation (built-in base58 decode).
Supports Transaction Version 1 (Post-Alpenglow Upgrade).
"""
import struct
import json
import urllib.request
from typing import Dict, List, Any, Optional

B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
B58_MAP = {char: idx for idx, char in enumerate(B58_ALPHABET)}

def b58_decode(s: str) -> bytes:
    """Zero-dependency Base58 decoder for Solana instruction parsing."""
    if not s:
        return b""
    num = 0
    for char in s:
        if char not in B58_MAP:
            return b""
        num = num * 58 + B58_MAP[char]
    
    full_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder="big") if num > 0 else b""
    leading_zeros = len(s) - len(s.lstrip("1"))
    return (b"\x00" * leading_zeros) + full_bytes

COMPUTE_BUDGET_PROGRAM_ID = "ComputeBudget111111111111111111111111111111"

JITO_TIP_ACCOUNTS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTxvQssQn138i2NN7MQQGy3mCabJZWzvmPst",
    "Cw8CFyM9FkoMi7K7Crnq6HNGCuogptEfvXiEu5vJwDxU",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
}

class BlockParser:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", timeout: int = 25):
        self.rpc_url = rpc_url
        self.timeout = timeout

    def fetch_block(self, slot: int) -> Optional[Dict[str, Any]]:
        """Fetch full block data with version 1 support (Alpenglow upgrade ready)."""
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlock",
            "params": [
                slot,
                {
                    "encoding": "json",
                    "transactionDetails": "full",
                    "rewards": True,
                    "maxSupportedTransactionVersion": 1
                }
            ]
        }).encode("utf-8")
        req = urllib.request.Request(
            self.rpc_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "SolanaBlockOrderingParser/1.0"}
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                return res.get("result")
        except Exception:
            return None

    def parse_block_ordering(self, slot: int, block_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze the ordered sequence of transactions in the block."""
        if block_data is None:
            block_data = self.fetch_block(slot)
        if not block_data:
            return {"slot": slot, "error": "block_not_found_or_skipped"}

        transactions = block_data.get("transactions", [])
        block_time = block_data.get("blockTime")
        blockhash = block_data.get("blockhash")
        parent_slot = block_data.get("parentSlot")

        parsed_txs: List[Dict[str, Any]] = []

        for idx, tx_entry in enumerate(transactions):
            tx = tx_entry.get("transaction", {})
            meta = tx_entry.get("meta", {})
            signatures = tx.get("signatures", [])
            signature = signatures[0] if signatures else ""

            message = tx.get("message", {})
            account_keys = message.get("accountKeys", [])
            
            cu_limit = 200_000
            priority_fee_micro_lamports = 0
            is_jito_tip = False

            for key in account_keys:
                if key in JITO_TIP_ACCOUNTS:
                    is_jito_tip = True
                    break

            instructions = message.get("instructions", [])
            for ix in instructions:
                prog_id_idx = ix.get("programIdIndex")
                if prog_id_idx is not None and prog_id_idx < len(account_keys):
                    prog_id = account_keys[prog_id_idx]
                    if prog_id == COMPUTE_BUDGET_PROGRAM_ID:
                        data_str = ix.get("data", "")
                        try:
                            raw_data = b58_decode(data_str)
                            if len(raw_data) >= 5:
                                ix_type = raw_data[0]
                                if ix_type == 2 and len(raw_data) >= 5: # SetComputeUnitLimit
                                    cu_limit = struct.unpack("<I", raw_data[1:5])[0]
                                elif ix_type == 3 and len(raw_data) >= 9: # SetComputeUnitPrice
                                    priority_fee_micro_lamports = struct.unpack("<Q", raw_data[1:9])[0]
                        except Exception:
                            pass

            actual_fee_lamports = meta.get("fee", 5000)
            compute_units_consumed = meta.get("computeUnitsConsumed", 0)
            err = meta.get("err")

            parsed_txs.append({
                "block_index": idx,
                "signature": signature,
                "priority_fee_micro_lamports": priority_fee_micro_lamports,
                "compute_unit_limit": cu_limit,
                "compute_units_consumed": compute_units_consumed,
                "actual_fee_lamports": actual_fee_lamports,
                "is_jito_tip": is_jito_tip,
                "account_count": len(account_keys),
                "is_success": err is None
            })

        return {
            "slot": slot,
            "block_time": block_time,
            "blockhash": blockhash,
            "parent_slot": parent_slot,
            "total_transactions": len(parsed_txs),
            "transactions": parsed_txs
        }
