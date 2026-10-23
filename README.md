# HireProof — Blockchain-Based Candidate Credential Verification

HireProof is a blockchain-based credential verification system designed to make academic and professional credential verification more transparent, secure, and reliable. It uses a Solidity smart contract to record credential information and support verification and revocation, while a React frontend and Flask backend provide an accessible interface for interacting with the system.

## Features

- **Credential Issuance:** Record candidate credentials on the blockchain.
- **Credential Verification:** Retrieve credential records and check their validity.
- **Credential Revocation:** Allow authorized users to revoke credentials.
- **Role-Based Access Control (RBAC):** Support controlled access for roles such as Admin, Issuer, and Verifier, according to the implemented contract permissions.
- **Blockchain Integration:** Interact with smart contracts through Web3.py.
- **Web Interface:** Use a React-based frontend to interact with the application.

## System Architecture

```text
React + Vite Frontend
        |
        v
     Flask API
        |
        v
   Web3.py Integration
        |
        v
 Solidity Smart Contract
        |
        v
    Blockchain
```

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, CSS |
| Backend | Python, Flask |
| Blockchain | Solidity, Hardhat |
| Blockchain Integration | Web3.py |
| Smart Contract Testing | Hardhat, TypeScript |

## Project Structure

```text
HireProof/
├── backend/
│   ├── app.py
│   └── setup_issuer.py
├── blockchain/
│   ├── contracts/
│   │   └── HireProof.sol
│   ├── ignition/
│   ├── test/
│   └── package.json
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
└── README.md
```

## Future Enhancements

- Integrate a wallet such as MetaMask.
- Improve role-specific dashboards and permissions.
- Support document hashing for integrity verification.
- Add credential history and audit logs.
- Explore deployment to a test network.

