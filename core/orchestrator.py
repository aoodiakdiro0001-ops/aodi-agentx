"""Aodı-AgentX — orchestrator: multi-agent flows (audit / test-gen / custom)."""
import json, os, sys, time, threading, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import scanner
import agents
import ollama_client

TASKS = {}          # id -> record (in-memory)
_TASKS_LOCK = threading.Lock()

_REPO_ROOT = Path(__file__).resolve().parent.parent   # مجلد المشروع aodi-agentx/


def _resolve_task_path(raw):
    """يحل المسار: مطلق ثمـ cwd ثم جذر الريبو — كي لا تتعثر واجهات بعيدة على مسارات نسبية."""
    p = Path(str(raw or ".")).expanduser()
    if p.is_absolute() and p.exists():
        return p.resolve()
    for base in (Path.cwd(), _REPO_ROOT, _REPO_ROOT.parent):
        c = (base / p)
        if c.exists():
            return c.resolve()
    return p.resolve()


def collect_files(root):
    root = Path(root).resolve()
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in config.SKIP_DIRS]
        for fn in filenames:
            if Path(fn).suffix in config.SCAN_EXTS:
                p = Path(dirpath) / fn
                try:
                    if p.stat().st_size <= config.MAX_FILE_BYTES:
                        files.append(p)
                except OSError:
                    pass
    return root, files


def static_findings(root, files):
    rels, out = [], []
    with ThreadPoolExecutor(max_workers=8) as ex:
        for row in ex.map(lambda p: (p, scanner.scan_file(p, str(p.relative_to(root)))), files):
            out.extend(row[1])
            rels.append(row[0])
    return rels, [scanner.to_dict(f) for f in out]


def _file_batches(root, files, chars=config.BATCH_CHARS):
    """يدمج ملفات متجاور النص في دفعات صغيرة استحكام اللمطابقة للذاكرة."""
    batches, cur, size = [], [], 0
    for p in sorted(files):
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")[: config.MAX_FILE_BYTES]
        except OSError:
            continue
        chunk = f"\n### FILE: {p.relative_to(root)}\n" + txt
        if size + len(chunk) > chars and cur:
            batches.append("\n".join(cur)); cur, size = [], 0
        cur.append(chunk); size += len(chunk)
    if cur:
        batches.append("\n".join(cur))
    return batches


def new_task(kind, kwargs):
    tid = uuid.uuid4().hex[:10]
    rec = {"id": tid, "kind": kind, "kwargs": {k: str(v) for k, v in kwargs.items()},
           "status": "queued", "created": time.strftime("%Y-%m-%d %H:%M:%S"),
           "result": None, "error": None}
    with _TASKS_LOCK:
        TASKS[tid] = rec
    config.log_task({"id": tid, "kind": kind, "args": rec["kwargs"], "status": "queued"})
    t = threading.Thread(target=_run_task, args=(tid,), daemon=True)
    t.start()
    return rec


def get_task(tid):
    with _TASKS_LOCK:
        return TASKS.get(tid)


def all_tasks():
    with _TASKS_LOCK:
        return list(TASKS.values())[::-1][:50]


def _set(tid, **kw):
    with _TASKS_LOCK:
        TASKS[tid].update(kw)


def _run_task(tid):
    rec = get_task(tid)
    if not rec:
        return
    kw = dict(rec["kwargs"])
    try:
        _set(tid, status="running", started=time.strftime("%Y-%m-%d %H:%M:%S"))
        kw["path"] = str(_resolve_task_path(kw.get("path", ".")))
        nodes = config.load_nodes()
        if not nodes:
            raise RuntimeError("لا عقد مسجلة — شغّل add-node أولاً (CLI: aodi-agentx add-node …)")
        flows = {"code_audit": _flow_audit, "test_gen": _flow_testgen, "custom": _flow_custom}
        fn = flows.get(rec["kind"])
        if not fn:
            raise RuntimeError(f"مهمة غير معروفة: {rec['kind']}")
        result = fn(kw, nodes)
        _set(tid, status="done", finished=time.strftime("%Y-%m-%d %H:%M:%S"), result=result)
        config.log_task({"id": tid, "kind": rec["kind"], "status": "done"})
    except Exception as e:
        _set(tid, status="failed", finished=time.strftime("%Y-%m-%d %H:%M:%S"),
             error=f"{type(e).__name__}: {e}")
        config.log_task({"id": tid, "kind": rec["kwargs"].get("kind"), "status": "failed",
                         "error": str(e)[:200]})


# -------------------------------------------------------------------- flows
def _flow_audit(kw, nodes):
    root, files = collect_files(kw["path"])
    if not files:
        raise RuntimeError(f"لا ملفات قابلة للتدقيق تحت {kw['path']}")
    rels, static = static_findings(root, files)
    batches = _file_batches(root, files)
    priorities = []
    rules_seen = {s["rule"] for s in static}
    prompt_meta = ("\nالعقد المكتشفة آلياً (اقرأها وحاكِم حقيقتها): "
                   + json.dumps(static, ensure_ascii=False)[:1200]
                   if static else "\nلم يشي الآلي شيئاً — فتّش بنفسك بأخطر الملفات.")
    jobs = [{"node_idx": i % len(nodes),
             "system": agents.AUDITOR,
             "prompt": (f"مقتطفات المشروع ({len(batches)} من النص):\n{b}\n{prompt_meta}\n"
                        "أخرج JSON فقط بحسب تعليمات النظام."),
             "expect_json": True}
            for i, b in enumerate(batches)]
    results = ollama_client.generate_many(nodes, jobs, max_workers=min(4, len(jobs)))
    llm_findings = []
    agents_used = []
    per_batch = []
    for i, r in enumerate(results):
        agents_used.append({"batch": i, "node": r["node"], "model": r["model"],
                            "ok": r["ok"], "latency_ms": r["latency_ms"],
                            "error": r["error"]})
        if not r["ok"]:
            continue
        try:
            parsed = json.loads(r["text"])
            arr = parsed.get("findings") if isinstance(parsed, dict) else None
            if isinstance(arr, list):
                for f in arr:
                    if isinstance(f, dict) and f.get("file"):
                        f.setdefault("severity", "med")
                        f.setdefault("message", "")
                        f.setdefault("suggestion", "")
                        f["source"] = "agent"
                        llm_findings.append(f)
                per_batch.append({"batch": i, "findings": len(arr or [])})
        except Exception:
            per_batch.append({"batch": i, "parse_error": r["text"][:120]})
    # يندمج ويؤكد بالرماية
    merged = list(static)
    for f in llm_findings:
        dup = any(f["file"] == m["file"] and f.get("line") == m.get("line")
                  for m in merged)
        if not dup:
            merged.append(f)
    return {
        "root": str(root),
        "files_scanned": len(files),
        "static_findings": len(static),
        "agent_findings": len(llm_findings),
        "total_findings": len(merged),
        "findings": merged,
        "agents": agents_used,
        "batches": per_batch,
        "stats": _summary(merged),
    }


def _flow_testgen(kw, nodes):
    root, files = collect_files(kw["path"])
    target = None
    if kw.get("target"):
        cand = [p for p in files if str(p.relative_to(root)) == str(kw["target"])]
        target = cand[0] if cand else None
    if target is None:
        py = [p for p in files if p.suffix == ".py" and not p.name.startswith("test")]
        target = py[0] if py else (files[0] if files else None)
    if target is None:
        raise RuntimeError("لم يتأكد ملف هدف للاختبارات")
    code = target.read_text(encoding="utf-8", errors="ignore")
    r = agents.run(agents.TESTER,
                   f"الملف: {target.relative_to(root)}\nالشطر:\n{code}",
                   nodes=nodes, temperature=0.2)
    if not r["ok"]:
        raise RuntimeError("فشل توليد الاختبار: " + (r["error"] or "غير معروف"))
    gen_dir = Path(root) / "generated_tests"
    gen_dir.mkdir(exist_ok=True)
    out_path = gen_dir / f"test_{target.stem}.py"
    out_path.write_text(r["text"] + "\n", encoding="utf-8")
    return {"root": str(root), "target": str(target.relative_to(root)),
            "written": str(out_path), "node": r["node"], "model": r["model"],
            "latency_ms": r["latency_ms"], "bytes": len(r["text"])}


def _flow_custom(kw, nodes):
    instruction = kw.get("instruction") or "نفّذ أفضل إجراء منطقي على المجلد."
    r = agents.run(agents.CUSTOM, instruction, nodes=nodes, temperature=0.3)
    if not r["ok"]:
        raise RuntimeError("فشل الوكيل: " + (r["error"] or "غير معروف"))
    return {"node": r["node"], "model": r["model"], "latency_ms": r["latency_ms"],
            "output": r["text"]}


def _summary(findings):
    by_sev = {}
    by_rule = {}
    for f in findings:
        by_sev[f["severity"]] = by_sev.get(f["severity"], 0) + 1
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    return {"by_severity": by_sev, "by_rule": by_rule}
