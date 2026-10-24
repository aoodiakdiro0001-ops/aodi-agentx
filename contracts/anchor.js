/**
 * Aodı-AgentX — anchor.js: ربط بصمة ملف/مجلد بمخفر الشبكة التجريبية (اختياري 100%).
 * Requires: npm i ethers  (فقط لو أراد المستخدم هذه الوحدة)
 * Usage: node contracts/anchor.js <sepolia-rpc-url> <private-key> <file-or-dir>
 */
const { ethers } = require("ethers");
const { createHash } = require("crypto");
const fs = require("fs");
const path = require("path");

const ABI = [
  "function anchor(bytes32 codeHash, string meta)",
  "function verify(bytes32) view returns (address owner, string meta, uint256 anchoredAt)",
];

function hashDir(dir) {
  const files = [];
  (function walk(d) {
    for (const f of fs.readdirSync(d)) {
      const p = path.join(d, f);
      if (fs.statSync(p).isDirectory()) { if (f !== ".git" && f !== "node_modules") walk(p); }
      else files.push(p);
    }
  })(dir);
  files.sort();
  const h = createHash("sha256");
  for (const p of files) {
    h.update(path.relative(dir, p)); h.update(fs.readFileSync(p));
  }
  return "0x" + h.digest("hex");
}

async function main() {
  const [, , rpc, pk, target] = process.argv;
  if (!rpc || !pk || !target) { console.error("الاستخدام: node anchor.js <rpc> <pk> <path>"); process.exit(1); }
  const stat = fs.statSync(target);
  const hash = stat.isDirectory() ? hashDir(target) : "0x" + createHash("sha256").update(fs.readFileSync(target)).digest("hex");
  const meta = `Aodı-AgentX proof — ${path.basename(target)} @ ${new Date().toISOString()}`;
  const provider = new ethers.JsonRpcProvider(rpc);
  const wallet = new ethers.Wallet(pk, provider);
  const addr = "0x0000000000000000000000000000000000000000"; // ← نشر عقدك ثم ضع عنوانه
  console.error("ضع عنوان العقد المنشورة AgentXProof في السطر أعلاه قبل التشغيل.");
  const c = new ethers.Contract(addr, ABI, wallet);
  const tx = await c.anchor(hash, meta);
  console.log("tx:", tx.hash, "hash:", hash, "meta:", meta);
  await tx.wait();
  console.log("✓ مثبْت على الشبكة التجريبية.");
}
main().catch((e) => { console.error(e); process.exit(1); });
