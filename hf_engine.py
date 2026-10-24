#!/usr/bin/env python3
"""Health-factor computation and protective action policy (category: health factor).

The engine reads monitored lending positions, computes the current health
factor from on-chain account liquidity, and when the factor crosses the
configured threshold it acts to prevent liquidation: repay debt, rebalance
collateral or adjust the position. Actions are real on-chain transactions.
"""
import json
import time
from pathlib import Path

from web3 import Web3

ACTION_LOG = Path(__file__).parent / "docs" / "actions-log.md"


def load_config(path):
    defaults = {
        "rpc": "https://data-seed-prebsc-2-s2.binance.org:8545",
        "chainId": 97,
        "threshold_repay": 1.20,
        "threshold_rebalance": 1.35,
        "positions": [],
        "dry_run": True,
    }
    try:
        with open(path) as f:
            defaults.update(json.load(f))
    except FileNotFoundError:
        pass
    return defaults


class HealthFactorEngine:
    def __init__(self, config):
        self.config = config
        self.w3 = Web3(Web3.HTTPProvider(config["rpc"]))
        self.last_action = None
        self.started = time.time()

    # ---- on-chain reads -------------------------------------------------
    def account_liquidity(self, position):
        """Read accountLiquidity (collateral - borrow) from a Comptroller."""
        comptroller = self.w3.eth.contract(
            address=Web3.to_checksum_address(position["comptroller"]),
            abi=[
                {
                    "constant": True,
                    "inputs": [{"name": "account", "type": "address"}],
                    "name": "getAccountLiquidity",
                    "outputs": [
                        {"name": "err", "type": "uint256"},
                        {"name": "collateral", "type": "uint256"},
                        {"name": "borrow", "type": "uint256"},
                    ],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function",
                }
            ],
        )
        _, collateral, borrow = comptroller.functions.getAccountLiquidity(
            Web3.to_checksum_address(position["wallet"])
        ).call()
        return collateral, borrow

    def health_factor(self, position):
        """HF = collateral / borrow. >1 is safe, <1 is liquidatable."""
        collateral, borrow = self.account_liquidity(position)
        if borrow == 0:
            return float("inf")
        return collateral / borrow

    # ---- protective actions (category: health factor) --------------------
    def act_repay(self, position, factor):
        """Repay debt to lift the health factor back above the safe line."""
        return self._execute(position, "repay", factor)

    def act_rebalance(self, position, factor):
        """Rebalance collateral to restore the target buffer."""
        return self._execute(position, "rebalance", factor)

    def act_adjust(self, position, factor):
        """Adjust the position (top-up collateral) to widen the margin."""
        return self._execute(position, "adjust", factor)

    def _execute(self, position, kind, factor):
        # Transaction signing/broadcast is wired to the operational wallet at
        # runtime; credentials never live in this repository.
        if self.config.get("dry_run", True):
            self._log(kind, position, factor, tx=None, note="dry-run")
            return {"action": kind, "executed": False, "mode": "dry-run"}
        tx = getattr(self, f"_tx_{kind}")(position)  # pragma: no cover
        self._log(kind, position, factor, tx=tx)
        return {"action": kind, "executed": True, "tx": tx}

    def _log(self, kind, position, factor, tx=None, note=None):
        ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        line = f"| {ts} | {kind} | {factor:.3f} | `{tx or 'pending'}` | {note or ''} |\n"
        ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        if not ACTION_LOG.exists():
            ACTION_LOG.write_text(
                "| time (UTC) | action | health factor at trigger | tx | note |\n"
                "|---|---|---|---|---|\n"
            )
        with open(ACTION_LOG, "a") as f:
            f.write(line)
        self.last_action = {"kind": kind, "factor": round(factor, 3), "tx": tx, "at": ts}

    # ---- loop and reports -------------------------------------------------
    def tick(self):
        for position in self.config.get("positions", []):
            factor = self.health_factor(position)
            if factor < self.config["threshold_repay"]:
                self.act_repay(position, factor)
            elif factor < self.config["threshold_rebalance"]:
                self.act_rebalance(position, factor)

    def report(self, position=None):
        positions = self.config.get("positions", [])
        if position:
            positions = [p for p in positions if p.get("id") == position]
        rows = []
        for p in positions:
            try:
                factor = self.health_factor(p)
                rows.append({
                    "id": p.get("id"),
                    "wallet": p.get("wallet"),
                    "health_factor": None if factor == float("inf") else round(factor, 3),
                    "safe": factor >= self.config["threshold_repay"],
                })
            except Exception as exc:
                rows.append({"id": p.get("id"), "error": str(exc), "safe": None})
        return {
            "category": "health factor",
            "positions": rows,
            "threshold_repay": self.config["threshold_repay"],
            "threshold_rebalance": self.config["threshold_rebalance"],
            "last_action": self.last_action,
        }

    def status(self):
        return {
            "agent": "Maria HealthFactor Sentinel",
            "agentId": 2662,
            "chainId": self.config["chainId"],
            "category": "health factor",
            "monitoring": "active" if self.w3.is_connected() else "rpc-down",
            "uptime_s": int(time.time() - self.started),
            "last_action": self.last_action,
        }
