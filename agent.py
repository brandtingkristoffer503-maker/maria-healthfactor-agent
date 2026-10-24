#!/usr/bin/env python3
"""Maria HealthFactor Sentinel — ERC-8004 agent on BNB Chain (agentId 2662).

Live agent service: serves the agent card, answers probes (A2A-style),
runs the health-factor monitoring loop and executes protective actions
(repay / rebalance / adjust) on BSC testnet when thresholds are crossed.
"""
import json
import os
import threading
import time
from pathlib import Path

from flask import Flask, jsonify, request

from hf_engine import HealthFactorEngine, load_config

CONFIG_PATH = os.environ.get("HF_CONFIG", str(Path(__file__).parent / "config.json"))
AGENT_ID = 2662
CHAIN_ID = 97
REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"

app = Flask(__name__)
config = load_config(CONFIG_PATH)
engine = HealthFactorEngine(config)


@app.get("/.well-known/agent-card.json")
@app.get("/agent-card.json")
def agent_card():
    card = json.loads((Path(__file__).parent / "card.json").read_text())
    return jsonify(card)


@app.get("/status")
def status():
    return jsonify(engine.status())


@app.post("/invoke")
def invoke():
    """A2A-style invocation: health-factor report for configured positions."""
    body = request.get_json(silent=True) or {}
    report = engine.report(position=body.get("position"))
    return jsonify({
        "agentId": AGENT_ID,
        "chainId": CHAIN_ID,
        "ok": True,
        "report": report,
    })


@app.get("/health")
def health():
    return jsonify({"ok": True, "agentId": AGENT_ID, "chainId": CHAIN_ID})


def monitor_loop():
    """Continuous watch: check positions, act when thresholds are crossed."""
    while True:
        try:
            engine.tick()
        except Exception as exc:  # keep the sentinel alive
            app.logger.error("monitor tick failed: %s", exc)
        time.sleep(int(os.environ.get("HF_INTERVAL", "300")))


if __name__ == "__main__":
    threading.Thread(target=monitor_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("HF_PORT", "8010")))
