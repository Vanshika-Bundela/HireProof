
import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { network } from "hardhat";
import { expect } from "chai";

describe("HireProof", async function () {
  const { ethers } = await network.connect();

  it("should issue and verify a credential", async function () {
    const [owner] = await ethers.getSigners();
    const factory = await ethers.getContractFactory("HireProof", owner);
    const contract = await factory.deploy();
    await contract.waitForDeployment();

    await contract.issueCredential(
      "HP-001",
      "Aarav Sharma",
      "B.Tech Computer Science",
      "Example University",
      "sample-hash-123"
    );

    const credential = await contract.verifyCredential("HP-001");

    assert.equal(credential.candidateName, "Aarav Sharma");
    assert.equal(credential.credentialName, "B.Tech Computer Science");
    assert.equal(credential.isValid, true);
  });

  it("should revoke a credential", async function () {
    const [owner] = await ethers.getSigners();
    const factory = await ethers.getContractFactory("HireProof", owner);
    const contract = await factory.deploy();
    await contract.waitForDeployment();

    await contract.issueCredential(
      "HP-002",
      "Aarav Sharma",
      "AI Certificate",
      "Example University",
      "sample-hash-456"
    );

    await contract.revokeCredential("HP-002");
    const credential = await contract.verifyCredential("HP-002");

    assert.equal(credential.isValid, false);
  });
});