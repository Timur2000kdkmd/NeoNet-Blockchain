// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Oracle is Ownable {
    // registered relayers (addresses that can submit aggregated reports)
    mapping(address => bool) public relayers;
    // registered signers (miners) that can endorse results
    mapping(address => bool) public signers;

    event RelayerAdded(address relayer);
    event RelayerRemoved(address relayer);
    event SignerAdded(address signer);
    event SignerRemoved(address signer);
    event ReportSubmitted(bytes32 indexed reportId, bytes32 indexed proposalId, bytes resultHash, address submittedBy);

    function addRelayer(address r) external onlyOwner {
        relayers[r] = true;
        emit RelayerAdded(r);
    }
    function removeRelayer(address r) external onlyOwner {
        relayers[r] = false;
        emit RelayerRemoved(r);
    }
    function addSigner(address s) external onlyOwner {
        signers[s] = true;
        emit SignerAdded(s);
    }
    function removeSigner(address s) external onlyOwner {
        signers[s] = false;
        emit SignerRemoved(s);
    }

    // verify ECDSA signatures for a message hash
    function _recoverSigner(bytes32 hash, bytes memory signature) internal pure returns (address) {
        // signature: r(32) + s(32) + v(1)
        require(signature.length == 65, "bad sig len");
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        return ecrecover(hash, v, r, s);
    }

    // Submit aggregated report for a proposal. The `signatures` parameter must contain ECDSA sigs
    // from at least `threshold` registered signers endorsing `reportId`.
    function submitReport(bytes32 proposalId, bytes32 reportId, bytes32 resultHash, bytes[] calldata signatures, uint256 threshold) external {
        require(relayers[msg.sender], "not relayer");
        // build message hash
        bytes32 msgHash = keccak256(abi.encodePacked(proposalId, reportId, resultHash));
        // require enough unique valid signers
        uint256 valid = 0;
        address lastSigner = address(0);
        for (uint i = 0; i < signatures.length; i++) {
            address signer = _recoverSigner(msgHash, signatures[i]);
            if (signer != address(0) && signers[signer] && signer != lastSigner) {
                valid += 1;
                lastSigner = signer;
            }
        }
        require(valid >= threshold, "not enough signatures");
        emit ReportSubmitted(reportId, proposalId, resultHash, msg.sender);
        // In practice, this event triggers governance execution or state change by watchers
    }
}
