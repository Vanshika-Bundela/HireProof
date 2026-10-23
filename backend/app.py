
from datetime import datetime
import hashlib
import json
import os

from flask import Flask, jsonify, request
from flask_cors import CORS
from web3 import Web3


# --------------------------------------------------
# Flask configuration
# --------------------------------------------------

app = Flask(__name__)
CORS(app)

# Maximum PDF upload size: 10 MB
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# --------------------------------------------------
# Blockchain configuration
# --------------------------------------------------

BLOCKCHAIN_URL = "http://127.0.0.1:8545"

CONTRACT_ADDRESS = Web3.to_checksum_address(
    "0x5FbDB2315678afecb367f032d93f642f64180aa3"
)

# Local Hardhat development account ONLY.
# Never use this private key on a real blockchain.
ISSUER_PRIVATE_KEY = (
    "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ARTIFACT_PATH = os.path.abspath(
    os.path.join(
        BASE_DIR,
        "..",
        "blockchain",
        "artifacts",
        "contracts",
        "HireProof.sol",
        "HireProof.json",
    )
)

HISTORY_FILE = os.path.join(
    BASE_DIR,
    "transaction_history.json",
)

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))
issuer = w3.eth.account.from_key(ISSUER_PRIVATE_KEY)


# --------------------------------------------------
# Load contract ABI
# --------------------------------------------------

if not os.path.exists(ARTIFACT_PATH):
    raise FileNotFoundError(
        f"Contract artifact not found: {ARTIFACT_PATH}. "
        "Compile HireProof.sol using Hardhat first."
    )

with open(ARTIFACT_PATH, "r", encoding="utf-8") as file:
    artifact = json.load(file)

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=artifact["abi"],
)


# --------------------------------------------------
# Blockchain helpers
# --------------------------------------------------

def ensure_blockchain_ready():
    """Check that Hardhat is running and the contract is deployed."""

    if not w3.is_connected():
        raise RuntimeError(
            "Cannot connect to Hardhat at "
            f"{BLOCKCHAIN_URL}. Start the Hardhat node first."
        )

    contract_code = w3.eth.get_code(CONTRACT_ADDRESS)

    if not contract_code or contract_code == b"":
        raise RuntimeError(
            f"No smart contract is deployed at {CONTRACT_ADDRESS}. "
            "Deploy HireProof.sol again and update CONTRACT_ADDRESS."
        )


def get_transaction_receipt(tx_hash):
    """Wait for a transaction and confirm that it succeeded."""

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise RuntimeError(
            f"Blockchain transaction failed: {tx_hash.hex()}"
        )

    return receipt


# --------------------------------------------------
# Transaction history helpers
# --------------------------------------------------

def load_history():
    """Load saved application transaction history."""

    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)

        return history if isinstance(history, list) else []

    except (json.JSONDecodeError, OSError):
        app.logger.exception("Could not read transaction history")
        return []


def save_history_entry(entry):
    """Save the newest transaction and keep at most 200 entries."""

    history = load_history()
    history.insert(0, entry)

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(history[:200], file, indent=2)


def record_transaction(
    event_type,
    credential_id,
    transaction_hash,
    candidate_name=None,
):
    entry = {
        "type": event_type,
        "credentialId": credential_id,
        "transactionHash": transaction_hash,
        "timestamp": datetime.now().astimezone().isoformat(),
    }

    if candidate_name:
        entry["candidateName"] = candidate_name

    save_history_entry(entry)


# --------------------------------------------------
# PDF hashing
# --------------------------------------------------

def get_pdf_hash():
    """Calculate SHA-256 hash of an uploaded PDF."""

    uploaded_file = request.files.get("document")

    if not uploaded_file or not uploaded_file.filename:
        raise ValueError("Please upload a PDF document.")

    if not uploaded_file.filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are accepted.")

    file_bytes = uploaded_file.read()

    if not file_bytes:
        raise ValueError("The uploaded file is empty.")

    # Basic signature check, not complete PDF validation.
    if not file_bytes.startswith(b"%PDF-"):
        raise ValueError(
            "The uploaded file does not appear to be a valid PDF."
        )

    return hashlib.sha256(file_bytes).hexdigest()


# --------------------------------------------------
# Issue a credential on the blockchain
# --------------------------------------------------

def issue_on_blockchain(data, document_hash):
    """Submit a credential issuance transaction."""

    ensure_blockchain_ready()

    credential_id = data["credentialId"].strip()

    transaction = contract.functions.issueCredential(
        credential_id,
        data["candidateName"].strip(),
        data["credentialName"].strip(),
        data["issuerName"].strip(),
        document_hash,
    ).build_transaction({
        "from": issuer.address,
        "nonce": w3.eth.get_transaction_count(
            issuer.address,
            "pending",
        ),
        "chainId": w3.eth.chain_id,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(
        transaction,
        private_key=ISSUER_PRIVATE_KEY,
    )

    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    get_transaction_receipt(tx_hash)

    return tx_hash.hex()


# --------------------------------------------------
# Revoke a credential on the blockchain
# --------------------------------------------------

def revoke_on_blockchain(credential_id):
    """Submit a credential revocation transaction."""

    ensure_blockchain_ready()

    transaction = contract.functions.revokeCredential(
        credential_id.strip()
    ).build_transaction({
        "from": issuer.address,
        "nonce": w3.eth.get_transaction_count(
            issuer.address,
            "pending",
        ),
        "chainId": w3.eth.chain_id,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })

    signed_tx = w3.eth.account.sign_transaction(
        transaction,
        private_key=ISSUER_PRIVATE_KEY,
    )

    tx_hash = w3.eth.send_raw_transaction(
        signed_tx.raw_transaction
    )

    get_transaction_receipt(tx_hash)

    return tx_hash.hex()


# --------------------------------------------------
# Read a credential from the blockchain
# --------------------------------------------------

def get_credential(credential_id):
    """Fetch and validate a credential lookup result."""

    ensure_blockchain_ready()

    credential_id = credential_id.strip()

    if not credential_id:
        raise ValueError("Credential ID cannot be empty.")

    try:
        result = contract.functions.verifyCredential(
            credential_id
        ).call()

    except Exception as error:
        app.logger.exception(
            "Smart contract lookup failed for credential %s",
            credential_id,
        )
        raise RuntimeError(
            "The smart contract could not return this credential. "
            "Check the contract ABI, deployed address, and "
            "verifyCredential function."
        ) from error

    if not result or not result[0]:
        raise LookupError(
            f"Credential '{credential_id}' does not exist "
            "on the current blockchain."
        )

    return result


# --------------------------------------------------
# Error handlers
# --------------------------------------------------

@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({
        "error": "File exceeds the 10 MB limit."
    }), 413


@app.errorhandler(500)
def internal_server_error(_error):
    return jsonify({
        "error": "An unexpected server error occurred."
    }), 500


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    connected = w3.is_connected()
    contract_deployed = False
    chain_id = None

    if connected:
        try:
            contract_code = w3.eth.get_code(CONTRACT_ADDRESS)
            contract_deployed = bool(contract_code)
            chain_id = w3.eth.chain_id
        except Exception:
            app.logger.exception("Blockchain health check failed")

    return jsonify({
        "status": "running",
        "blockchain_connected": connected,
        "contract_deployed": contract_deployed,
        "contract_address": CONTRACT_ADDRESS,
        "chain_id": chain_id,
        "issuer_address": issuer.address,
    })


# --------------------------------------------------
# Issue using a manually supplied hash
# --------------------------------------------------

@app.route("/api/credentials", methods=["POST"])
def issue_credential_with_hash():
    data = request.get_json(silent=True) or {}

    required = [
        "credentialId",
        "candidateName",
        "credentialName",
        "issuerName",
        "credentialHash",
    ]

    if any(
        not isinstance(data.get(field), str)
        or not data[field].strip()
        for field in required
    ):
        return jsonify({
            "error": "All credential fields are required."
        }), 400

    try:
        credential_id = data["credentialId"].strip()
        candidate_name = data["candidateName"].strip()
        credential_hash = data["credentialHash"].strip()

        tx_hash = issue_on_blockchain(
            data,
            credential_hash,
        )

        record_transaction(
            "Credential Issued",
            credential_id,
            tx_hash,
            candidate_name,
        )

        return jsonify({
            "message": "Credential issued successfully.",
            "credentialId": credential_id,
            "credentialHash": credential_hash,
            "transactionHash": tx_hash,
        }), 201

    except Exception as error:
        app.logger.exception("Credential issuance failed")

        return jsonify({
            "error": str(error)
        }), 400


# --------------------------------------------------
# Hash a PDF without issuing a credential
# --------------------------------------------------

@app.route("/api/hash-document", methods=["POST"])
def hash_document():
    try:
        document_hash = get_pdf_hash()

        return jsonify({
            "message": "Document hashed successfully.",
            "algorithm": "SHA-256",
            "credentialHash": document_hash,
        }), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400


# --------------------------------------------------
# Issue a credential using an uploaded PDF
# --------------------------------------------------

@app.route("/api/credentials/with-document", methods=["POST"])
def issue_credential_with_document():
    data = request.form

    required = [
        "credentialId",
        "candidateName",
        "credentialName",
        "issuerName",
    ]

    if any(
        not data.get(field, "").strip()
        for field in required
    ):
        return jsonify({
            "error": "All credential fields are required."
        }), 400

    try:
        credential_id = data["credentialId"].strip()
        candidate_name = data["candidateName"].strip()

        document_hash = get_pdf_hash()

        tx_hash = issue_on_blockchain(
            data,
            document_hash,
        )

        record_transaction(
            "Credential Issued",
            credential_id,
            tx_hash,
            candidate_name,
        )

        return jsonify({
            "message": "Credential issued successfully.",
            "credentialId": credential_id,
            "algorithm": "SHA-256",
            "credentialHash": document_hash,
            "transactionHash": tx_hash,
        }), 201

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except Exception as error:
        app.logger.exception("PDF credential issuance failed")

        return jsonify({
            "error": str(error)
        }), 400


# --------------------------------------------------
# Get a credential's on-chain details
# --------------------------------------------------

@app.route("/api/credentials/<credential_id>", methods=["GET"])
def verify_credential(credential_id):
    try:
        result = get_credential(credential_id)

        return jsonify({
            "credentialId": result[0],
            "candidateName": result[1],
            "credentialName": result[2],
            "issuerName": result[3],
            "credentialHash": result[4],
            "issueDate": result[5],
            "isValid": bool(result[6]),
        }), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except LookupError as error:
        return jsonify({
            "error": str(error),
            "credentialId": credential_id,
        }), 404

    except Exception as error:
        app.logger.exception(
            "Credential lookup failed for ID: %s",
            credential_id,
        )

        return jsonify({
            "error": str(error),
            "credentialId": credential_id,
        }), 500


# --------------------------------------------------
# Verify an uploaded PDF against an on-chain hash
# --------------------------------------------------

@app.route(
    "/api/credentials/<credential_id>/verify-document",
    methods=["POST"],
)
def verify_document(credential_id):
    try:
        result = get_credential(credential_id)

        uploaded_hash = get_pdf_hash()
        stored_hash = result[4]

        document_matches = uploaded_hash == stored_hash
        credential_valid = bool(result[6])

        successful = (
            document_matches and credential_valid
        )

        if successful:
            message = (
                "Document matches and credential is valid."
            )
        elif not document_matches:
            message = "Document hash mismatch."
        else:
            message = (
                "Document matches, but the credential "
                "has been revoked."
            )

        return jsonify({
            "credentialId": result[0],
            "algorithm": "SHA-256",
            "documentMatches": document_matches,
            "credentialValid": credential_valid,
            "verificationSuccessful": successful,
            "message": message,
        }), 200

    except ValueError as error:
        return jsonify({
            "error": str(error)
        }), 400

    except LookupError as error:
        return jsonify({
            "error": str(error),
            "credentialId": credential_id,
        }), 404

    except Exception as error:
        app.logger.exception(
            "Document verification failed for ID: %s",
            credential_id,
        )

        return jsonify({
            "error": str(error),
            "credentialId": credential_id,
        }), 500


# --------------------------------------------------
# Revoke a credential
# --------------------------------------------------

@app.route(
    "/api/credentials/<credential_id>/revoke",
    methods=["POST"],
)
def revoke_credential(credential_id):
    try:
        # Check that the credential exists before revoking it.
        result = get_credential(credential_id)

        if not bool(result[6]):
            return jsonify({
                "error": "This credential has already been revoked."
            }), 400

        tx_hash = revoke_on_blockchain(credential_id)

        record_transaction(
            "Credential Revoked",
            credential_id,
            tx_hash,
            result[1],
        )

        return jsonify({
            "message": "Credential revoked successfully.",
            "credentialId": credential_id,
            "transactionHash": tx_hash,
        }), 200

    except LookupError as error:
        return jsonify({
            "error": str(error)
        }), 404

    except Exception as error:
        app.logger.exception(
            "Credential revocation failed for ID: %s",
            credential_id,
        )

        return jsonify({
            "error": str(error)
        }), 400


# --------------------------------------------------
# Dashboard statistics and recent transactions
# --------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
def dashboard():
    history = load_history()

    issued_ids = {
        item.get("credentialId")
        for item in history
        if item.get("type") == "Credential Issued"
        and item.get("credentialId")
    }

    revoked_ids = {
        item.get("credentialId")
        for item in history
        if item.get("type") == "Credential Revoked"
        and item.get("credentialId")
    }

    return jsonify({
        "totalIssued": len(issued_ids),
        "totalRevoked": len(issued_ids & revoked_ids),
        "activeCredentials": len(issued_ids - revoked_ids),
        "recentTransactions": history[:10],
    }), 200


# --------------------------------------------------
# Run Flask
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
