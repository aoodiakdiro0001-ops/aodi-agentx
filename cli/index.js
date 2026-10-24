#!/usr/bin/env node
/**
 * Aodı-AgentX CLI — zero-dependency (Node 18+).
 * أوامر: init | add-node | nodes | run | task | tasks | report | doctor
 */
const fs = require("fs");
const path = require("path");
const http = require("http");
const os = require("os");

const HOME_FILE = path.join(os.homedir(), ".aodix", "cli.json");
const VERSION = "1.0.0";
const C = { g: "\x1b[32m", y: "\x1b[33m", r: "\x1b[31m", b: "\x1b[36m", x: "\x1b[0m", bold: "\x1b[1m" };

function apiBase() {
  const cfg = fs.existsSync(HOME_FILE) ? JSON.parse(fs.readFileSync(HOME_FILE, "utf8")) : {};
  return process.env.AODX_API || cfg.api || "http://127.0.0.1:8787";
}
function saveApi(api) {
  fs.mkdirSync(path.dirname(HOME_FILE), { recursive: true });
  fs.writeFileSync(HOME_FILE, JSON.stringify({ ...readCfg(), api }, null, 1));
}
function readCfg() {
  try { return JSON.parse(fs.readFileSync(HOME_FILE, "utf8")); } catch { return {}; }
}
function req(method, url, body) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const data = body ? Buffer.from(JSON.stringify(body)) : null;
    const r = http.request({ hostname: u.hostname, port: u.port || 80, path: u.pathname + u.search,
      method, headers: data ? { "Content-Type": "application/json", "Content-Length": data.length } : {},
      timeout: 600000 }, (res) => {
      let buf = "";
      res.on("data", (c) => (buf += c));
      res.on("end", () => { try { resolve({ code: res.statusCode, json: JSON.parse(buf) }); }
        catch { resolve({ code: res.statusCode, text: buf }); } });
    });
    r.on("error", (e) => resolve({ code: 0, err: String(e) }));
    r.on("timeout", () => { r.destroy(); resolve({ code: 0, err: "timeout" }); });
    if (data) r.write(data);
    r.end();
  });
}
const say = (t) => console.log(t);

async function cmdInit() {
  const base = apiBase();
  const h = await req("GET", base + "/api/health");
  if (h.code === 0) {
    say(`${C.r}[✗] core لا يرد على ${base}${C.x}`);
    say(`    شغّل: python3 core/server.py --port 8787   ثم أعد: aodi-agentx init`);
    process.exit(1);
  }
  const ok = (h.json.nodes || []).filter((n) => n.ok);
  say(`${C.g}[✓] ${h.json.brand} v${h.json.version}${C.x}`);
  say(`العقد الصحيحة: ${ok.length}/${(h.json.nodes || []).length}`);
  (h.json.nodes || []).forEach((n) => {
    say(`${n.ok ? C.g + "[✓]" : C.r + "[✗]"} ${C.b}${n.name}${C.x} ${n.url}${n.ok ? ` · ${n.latency_ms}ms · ${n.model || "×"}` : ` · ${n.error || ""}`}`);
  });
  say(`\nTouch: ${C.b}${HOME_FILE}${C.x}`);
  if (!fs.existsSync(HOME_FILE)) saveApi(base);
}

async function cmdAddNode(name, url, model) {
  const r = await req("POST", apiBase() + "/api/nodes", { name, url, model });
  if (r.code === 400 && r.json && r.json.error) {
    say(`${C.r}[✗] ${r.json.error}${C.x} (${r.json.probe || ""})`);
    process.exit(1);
  }
  say(`${C.g}[✓] عقدة أُضيفت: ${name} → ${url}${C.x}`);
  if (r.json.probe) say(`    زمن اكتشاف: ${r.json.probe.latency_ms}ms · نماذج: ${(r.json.probe.models || []).join(", ")}`);
}

async function cmdNodes() {
  const r = await req("GET", apiBase() + "/api/health");
  r.json.nodes.forEach((n) =>
    say(`${n.ok ? C.g + "[✓]" : C.r + "[✗]"} ${C.b}${n.name}${C.x} ${n.url} ${n.ok ? `· ${n.latency_ms}ms · ${n.model}` : C.r + "·" + (n.error || "لا رد") + C.x}`));
}

async function cmdRun(args) {
  const kind = args._[1] || "code_audit";
  let targetArg = null, instruction = null;
  const rest = args._.slice(2);
  for (let i = 0; i < rest.length; i++) {
    if (rest[i] === "--path") targetArg = ["path", rest[++i]];
    else if (rest[i] === "--target") targetArg = ["target", rest[++i]];
    else if (rest[i] === "--instruction") instruction = rest[++i];
    else if (!instruction) { instruction = rest[i]; }
  }
  const body = { kind };
  if (targetArg) body[targetArg[0]] = targetArg[1];
  if (instruction && kind === "custom") body.instruction = instruction;
  const r = await req("POST", apiBase() + "/api/tasks", body);
  if (r.json && r.json.id) {
    say(`${C.y}[▸] مهمة ${C.b}${r.json.id}${C.x} من نوع ${kind} — تنفيذ موازٍ…`);
    for (let i = 0; i < 600; i++) {
      await new Promise((s) => setTimeout(s, 2000));
      const t = await req("GET", apiBase() + "/api/tasks/" + r.json.id);
      const s = t.json && t.json.status;
      if (s === "done" || s === "failed") { await printTask(r.json.id); return; }
      process.stdout.write(C.y + "•" + C.x);
    }
  } else say(`${C.r}[✗] ${(r.json && r.json.error) || "core لا يرد"}${C.x}`);
}

async function printTask(id) {
  const t = await req("GET", apiBase() + "/api/tasks/" + id);
  const j = t.json || {};
  if (j.error) return say(`${C.r}[✗] ${j.error}${C.x}`);
  if (j.status === "done") { say(`\n${C.g}[✓] انتهت${C.x}`); printReport(j.result || j); }
  else say(`\n${C.r}[✗] فشلت: ${j.error || ""}${C.x}`);
}

function printReport(res) {
  if (!res) return;
  if (res.total_findings !== undefined) {
    say(`\n${C.bold}تدقيق ${res.root}${C.x}`);
    say(`الملفات: ${res.files_scanned} · آلي: ${res.static_findings} · وكلاء: ${res.agent_findings} · إجمالي: ${C.bold}${res.total_findings}${C.x}`);
    (res.findings || []).sort((a, b) => (a.severity > b.severity ? 1 : -1)).forEach((f) => {
      const tag = f.severity === "high" ? C.r : f.severity === "med" ? C.y : C.b;
      say(`${tag}[${f.severity.toUpperCase()}]${C.x} ${f.file}:${f.line} ${C.b}${f.rule}${C.x} ${f.message || ""}`);
      if (f.suggestion) say(`      ↳ ${f.suggestion}`);
    });
    say(`\nعوامل: ${(res.agents || []).map((a) => `${a.node}(${a.model},${a.latency_ms}ms)`).join(" · ")}`);
  } else if (res.written) {
    say(`${C.g}[✓] اختبارات كُتبت: ${C.b}${res.written}${C.x} (${res.node}/${res.model})`);
  } else if (res.output) {
    say(res.output);
  } else say(JSON.stringify(res, null, 1));
}

async function cmdTasks() {
  const r = await req("GET", apiBase() + "/api/tasks");
  (r.json.tasks || []).forEach((t) =>
    say(`${C.b}${t.id}${C.x} ${t.kind} ${t.status === "done" ? C.g + "done" : t.status === "failed" ? C.r + "failed" : C.y + t.status}${C.x} ${t.created}`));
}

async function main() {
  const raw = process.argv.slice(2);
  const args = { _: raw.filter((x) => !x.startsWith("--")) };
  if (!raw.length || raw[0] === "help" || raw[0] === "--help") {
    say(`${C.b}aodi-agentx v${VERSION}${C.x} — distributed AI operations`);
    say(`  init                                  اكتشاف العقد`);
    say(`  add-node <name> <url> [model]         تسجيل عقدة Ollama`);
    say(`  nodes                                  حالة العقد والصحة`);
    say(`  run code_audit --path <dir>            فحص أمني متعدد الوكلاء`);
    say(`  run test_gen --path <dir> [--target f] توليد اختبارات للوحدات`);
    say(`  run custom "<instruction>"             مهمة حرة عبر أقرب وكيل`);
    say(`  tasks / task-report <id>               متابعة المهام`);
    say(`  doctor                                 فحص شامل سريع`);
    say(`\n  بيئة: AODX_API (افتراضي http://127.0.0.1:8787)`);
    return;
  }
  switch (raw[0]) {
    case "init": return cmdInit();
    case "add-node": return cmdAddNode(raw[1], raw[2], raw[3]);
    case "nodes": return cmdNodes();
    case "run": return cmdRun({ _: ["run", ...raw.slice(1)] });
    case "tasks": return cmdTasks();
    case "task-report": { const id = raw[1]; if (id) await printTask(id); return; }
    case "doctor": {
      const base = apiBase();
      say(`${C.b}Aodı-AgentX doctor${C.x}`);
      say(`core: ${base}`);
      await cmdInit();
      return;
    }
    default: say(`${C.r}أمر غير معروف: ${raw[0]}${C.x} — جرّب aodi-agentx help`);
  }
}

main().catch((e) => { say(`${C.r}خطأ: ${e}${C.x}`); process.exit(1); });
