"""Cluster probing module: discovers validator nodes, client software, and version strings.
"""
import json
import urllib.request
from typing import Dict, List, Any, Optional

class ClusterProbe:
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com", timeout: int = 15):
        self.rpc_url = rpc_url
        self.timeout = timeout

    def _rpc_call(self, method: str, params: Optional[List[Any]] = None) -> Any:
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or []
        }).encode("utf-8")
        req = urllib.request.Request(
            self.rpc_url,
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "SolanaBlockOrderingProbe/1.0"}
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "error" in data:
                raise RuntimeError(f"RPC Error [{method}]: {data['error']}")
            return data.get("result")

    def get_cluster_nodes(self) -> List[Dict[str, Any]]:
        """Fetch all active cluster nodes and their version strings."""
        return self._rpc_call("getClusterNodes") or []

    def classify_validators_by_client(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group cluster nodes by client family and version."""
        nodes = self.get_cluster_nodes()
        classified: Dict[str, List[Dict[str, Any]]] = {}
        for node in nodes:
            version = node.get("version") or "unknown"
            pubkey = node.get("pubkey")
            tpu = node.get("tpu")
            if not tpu:
                continue # Skip non-TPU / passive RPC nodes
            
            # Identify family: Jito, Agave, Frankendancer, etc.
            family = "Agave"
            if "jito" in version.lower():
                family = "Jito-Solana"
            elif "firedancer" in version.lower() or "frankendancer" in version.lower():
                family = "Firedancer/Frankendancer"
            
            client_key = f"{family} ({version})"
            if client_key not in classified:
                classified[client_key] = []
            classified[client_key].append(node)
        return classified

    def select_representative_validators(self, count_per_version: int = 2) -> List[Dict[str, Any]]:
        """Select at least 6 representative validators spanning >= 3 client versions."""
        classified = self.classify_validators_by_client()
        selected: List[Dict[str, Any]] = []
        
        # Sort version groups by validator count descending
        sorted_groups = sorted(classified.items(), key=lambda x: len(x[1]), reverse=True)
        for client_name, nodes in sorted_groups:
            picked = nodes[:count_per_version]
            for node in picked:
                node["client_classification"] = client_name
                selected.append(node)
            if len(selected) >= 6 and len(sorted_groups) >= 3:
                break
        return selected
