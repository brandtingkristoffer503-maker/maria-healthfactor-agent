# Maria HealthFactor Sentinel

ERC-8004 registered autonomous agent on BNB Chain. **Category: health factor.**

Monitors lending-position health factors on BNB Smart Chain and acts to prevent
liquidation: repays debt, rebalances collateral and adjusts positions when
thresholds are crossed. Every action is recorded on-chain.

## On-chain identity

| Field | Value |
|---|---|
| Standard | ERC-8004 (Trustless Agents) |
| Registry | `0x8004A818BFB912233c491871b3d84c89A494BD9e` |
| Chain | **BSC Testnet (chainId 97)** |
| Agent ID | **2662** |
| Owner wallet | `0x893Ce167AACEf83F2b6cCA8BA51d593d797c88Bc` |
| Registration tx | `0xcc95d9c8b7defff459d7d85c2d5630172585c2d59b40cc77860407e69d9d4069` |
| Agent card | https://maria-hf-agent.netlify.app/.well-known/agent-card.json |

## What it does

1. Watches collateral health factors on BSC lending markets.
2. When a position's health factor crosses the risk threshold, the agent acts:
   repays debt, rebalances collateral or adjusts the position.
3. Each action is a real on-chain transaction from the agent's operational wallet.
4. Probes are answered live over HTTP (A2A-style agent card + status endpoints).

## Endpoints

Live service (always on, deployed behind TLS on our own infrastructure):

- `https://137-74-165-236.sslip.io/hf-agent/status` — monitoring status
- `https://137-74-165-236.sslip.io/hf-agent/invoke` — A2A invocation (health-factor report)
- `https://137-74-165-236.sslip.io/hf-agent/agent-card.json` — agent card served live

Static hosting (agent card + landing):

- `GET /.well-known/agent-card.json` — EIP-8004 / A2A agent card
- `GET /status` — monitoring status, monitored positions, last action
- `POST /invoke` — A2A invocation: returns a health-factor report for configured positions

## Run

```bash
pip install -r requirements.txt
python3 agent.py            # listens on :8010
```

Configuration via environment variables (see `config.example.json`). Operational
keys are injected at runtime from an encrypted vault; no keys are stored in this repo.

## Repo layout

- `agent.py` — the live agent service (HTTP + monitoring loop)
- `hf_engine.py` — health-factor computation and action policy
- `card.json` — agent card copy served at the registered domain
- `registry_check.py` — verifies the ERC-8004 registration on-chain
- `docs/actions-log.md` — log of on-chain actions (updated as the agent acts)

Built for the BNB Chain Set and Earn campaign (Oct-Nov 2026).
