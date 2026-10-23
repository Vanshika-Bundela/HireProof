
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract HireProof {
    struct Credential {
        string credentialId;
        string candidateName;
        string credentialName;
        string issuerName;
        string credentialHash;
        uint256 issueDate;
        bool isValid;
    }

    address public admin;

    mapping(address => bool) public isIssuer;
    mapping(string => Credential) private credentials;
    mapping(string => bool) private credentialExists;
    mapping(string => address) public credentialIssuer;

    event IssuerAuthorized(address indexed issuer);
    event IssuerRemoved(address indexed issuer);

    event CredentialIssued(
        string indexed credentialId,
        address indexed issuer,
        uint256 issueDate
    );

    event CredentialRevoked(
        string indexed credentialId,
        address indexed revokedBy
    );

    constructor() {
        admin = msg.sender;
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier onlyIssuer() {
        require(isIssuer[msg.sender], "Only authorized issuers can perform this action");
        _;
    }

    function authorizeIssuer(address _issuer) public onlyAdmin {
        require(_issuer != address(0), "Invalid issuer address");
        require(!isIssuer[_issuer], "Address is already an issuer");

        isIssuer[_issuer] = true;
        emit IssuerAuthorized(_issuer);
    }

    function removeIssuer(address _issuer) public onlyAdmin {
        require(isIssuer[_issuer], "Address is not an issuer");

        isIssuer[_issuer] = false;
        emit IssuerRemoved(_issuer);
    }

    function issueCredential(
        string memory _credentialId,
        string memory _candidateName,
        string memory _credentialName,
        string memory _issuerName,
        string memory _credentialHash
    ) public onlyIssuer {
        require(bytes(_credentialId).length > 0, "Credential ID is required");
        require(bytes(_candidateName).length > 0, "Candidate name is required");
        require(bytes(_credentialName).length > 0, "Credential name is required");
        require(bytes(_issuerName).length > 0, "Issuer name is required");
        require(bytes(_credentialHash).length > 0, "Credential hash is required");
        require(!credentialExists[_credentialId], "Credential already exists");

        credentials[_credentialId] = Credential({
            credentialId: _credentialId,
            candidateName: _candidateName,
            credentialName: _credentialName,
            issuerName: _issuerName,
            credentialHash: _credentialHash,
            issueDate: block.timestamp,
            isValid: true
        });

        credentialExists[_credentialId] = true;
        credentialIssuer[_credentialId] = msg.sender;

        emit CredentialIssued(
            _credentialId,
            msg.sender,
            block.timestamp
        );
    }

    function verifyCredential(
        string memory _credentialId
    ) public view returns (Credential memory) {
        require(credentialExists[_credentialId], "Credential not found");
        return credentials[_credentialId];
    }

    function revokeCredential(
        string memory _credentialId
    ) public {
        require(credentialExists[_credentialId], "Credential not found");
        require(
            msg.sender == admin ||
            (isIssuer[msg.sender] &&
                credentialIssuer[_credentialId] == msg.sender),
            "Not authorized to revoke this credential"
        );
        require(credentials[_credentialId].isValid, "Credential already revoked");

        credentials[_credentialId].isValid = false;

        emit CredentialRevoked(_credentialId, msg.sender);
    }
}