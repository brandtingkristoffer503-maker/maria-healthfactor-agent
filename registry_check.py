#!/usr/bin/env python3
"""Verify the ERC-8004 registration of agent 2662 on BSC testnet (chain 97)."""
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://data-seed-prebsc-2-s2.binance.org:8545"))
REGISTRY = "0x8004A818BFB912233c491871b3d84c89A494BD9e"
OWNER = "0x893Ce167AACEf83F2b6cCA8BA51d593d797c88Bc"
AGENT_ID = 2662

abi = [
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "ownerOf",
     "outputs": [{"name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "tokenURI",
     "outputs": [{"name": "", "type": "string"}], "stateMutability": "view", "type": "function"},
]
registry = w3.eth.contract(address=Web3.to_checksum_address(REGISTRY), abi=abi)
owner = registry.functions.ownerOf(AGENT_ID).call()
uri = registry.functions.tokenURI(AGENT_ID).call()
print(f"agentId {AGENT_ID}: owner={owner}")
print(f"owner match: {owner.lower() == OWNER.lower()}")
print(f"agentURI: {uri}")
