
import { buildModule } from "@nomicfoundation/hardhat-ignition/modules";

const HireProofAccessControlModule = buildModule(
  "HireProofAccessControlModule",
  (m) => {
    const hireProof = m.contract("HireProof");
    return { hireProof };
  }
);

export default HireProofAccessControlModule;