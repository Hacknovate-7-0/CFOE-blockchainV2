import sys
sys.path.insert(0, 'd:/projects compiled/CFOE-blockchain/cfoe-blockchain/projects/cfoe-blockchain')

from blockchain_client import get_blockchain_client

bc = get_blockchain_client()
print(f"Connected: {bc.connected}")
print(f"Wallet connected: {bc.wallet_connected}")
print(f"Address: {bc.address}")

# Test anchor_score
result = bc.anchor_score(
    supplier_name="Test Corp",
    risk_score=0.45,
    classification="Moderate Risk",
    emissions=2100,
    violations=2
)

print(f"\nAnchor result:")
print(f"  TX ID: {result.get('tx_id')}")
print(f"  Local ID: {result.get('local_id')}")
print(f"  On chain: {result.get('on_chain')}")
