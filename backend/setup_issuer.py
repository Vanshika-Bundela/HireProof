
import json
import os
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))


CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93f642f64180aa3"
)


ADMIN_PRIVATE_KEY = (
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
)

# Hardhat's second local test account
ISSUER_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)

artifact_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "blockchain",
    "artifacts",
    "contracts",
    "HireProof.sol",
    "HireProof.json"
)

with open(artifact_path, "r", encoding="utf-8") as file:
    artifact = json.load(file)

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=artifact["abi"]
)

admin = w3.eth.account.from_key(ADMIN_PRIVATE_KEY)
issuer = w3.eth.account.from_key(ISSUER_PRIVATE_KEY)

transaction = contract.functions.authorizeIssuer(
    issuer.address
).build_transaction({
    "from": admin.address,
    "nonce": w3.eth.get_transaction_count(admin.address),
    "chainId": w3.eth.chain_id,
    "gas": 200000
})

signed_tx = w3.eth.account.sign_transaction(
    transaction,
    private_key=ADMIN_PRIVATE_KEY
)

print("Connected:", w3.is_connected())
print("Chain ID:", w3.eth.chain_id)
print("Contract address:", contract.address)
print("Admin address:", admin.address)
print("Transaction sender:", transaction["from"])
print("Sender balance (wei):", w3.eth.get_balance(transaction["from"]))
print("Transaction gas:", transaction["gas"])
print("Transaction gas price:", transaction.get("gasPrice"))
print("Contract code length:", len(w3.eth.get_code(contract.address)))
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print("Contract:", contract.address)
print("Admin:", admin.address)
print("Issuer:", issuer.address)
print("Transaction sender:", transaction["from"])
print("Sender balance:", w3.eth.get_balance(transaction["from"]))
print("Contract code bytes:", len(w3.eth.get_code(contract.address)))
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status == 1:
    print("Issuer authorized successfully!")
    print("Issuer address:", issuer.address)
    print("Transaction hash:", tx_hash.hex())
else:
    print("Issuer authorization failed.")