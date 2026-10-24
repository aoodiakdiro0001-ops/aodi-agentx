// Aodı-AgentX — Verification Layer (optional plugin)
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title AgentXProof
/// @notice يسجّل بصمات الأكواد وتقارير التدقيق على شبكة تجربة (Sepolia/Amoy)
///         لإثبات ملكيتها وعدم التلاعب بها — مالك كل بصمة قابل للتحقق بلا وسيط.
contract AgentXProof {
    struct Proof {
        address owner;
        string  meta;      // وصف عربي قصير للمادة المقيدعة (اسم المشروع/التبويب)
        uint256 blockTime;
    }

    // خريطة البصمة: keccak(bytes32 hash messaging) — البصمة تأتي خارجياً sha256 hex من Aodı-AgentX.
    mapping(bytes32 => Proof) private proofs;
    address public admin;
    event Anchored(bytes32 indexed hash, address indexed owner, string meta, uint256 time);

    error AlreadyAnchored();

    constructor() { admin = msg.sender; }

    /// تسجيل بصمة كود/تقرير (hex string البصمة من Aodı-AgentX).
    function anchor(bytes32 codeHash, string calldata meta) external {
        if (proofs[codeHash].owner != address(0)) revert AlreadyAnchored();
        proofs[codeHash] = Proof(msg.sender, meta, block.timestamp);
        emit Anchored(codeHash, msg.sender, meta, block.timestamp);
    }

    /// استعلام إثبات: من ربط هذه البصمة ومتى.
    function verify(bytes32 codeHash)
        external view returns (address owner, string memory meta, uint256 anchoredAt)
    {
        Proof storage p = proofs[codeHash];
        return (p.owner, p.meta, p.blockTime);
    }
}
