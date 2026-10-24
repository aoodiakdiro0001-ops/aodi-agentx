"""Aodı-AgentX — optional FastAPI wrapper لنفس منطق stdlib server (اختياري 100%)."""
import json
from pathlib import Path

import fastapi
import uvicorn

import config
import ollama_client
import orchestrator

app = fastapi.FastAPI(title=config.BRAND, version=config.VERSION)
_dsh = Path(__file__).resolve().parent.parent / "dashboard"


@app.get("/api/health")
def health():
    return {"brand": config.BRAND, "version": config.VERSION,
            "nodes": ollama_client.health()}


@app.get("/api/nodes")
def nodes():
    return {"nodes": config.load_nodes()}


@app.post("/api/nodes")
def add_node(body: dict):
    name, url = (body.get("name") or "").strip(), (body.get("url") or "").strip()
    if not name or not url:
        raise fastapi.HTTPException(400, "name و url مطلوبان")
    probe = ollama_client.ping_node(url)
    if not probe["ok"]:
        return {"error": "الرابط لا يرد", "probe": probe["error"]}
    ns = [n for n in config.load_nodes() if n.get("name") != name]
    ns.append(dict(name=name, url=url, model=body.get("model") or None,
                   tags=body.get("tags", [])))
    config.save_nodes(ns)
    return {"ok": True, "nodes": ns, "probe": probe}


@app.post("/api/nodes/remove")
def rm_node(body: dict):
    ns = [n for n in config.load_nodes() if n.get("name") != body.get("name")]
    config.save_nodes(ns)
    return {"ok": True, "nodes": ns}


@app.post("/api/tasks")
def new_task(body: dict):
    kind = body.get("kind") or "custom"
    if kind not in ("code_audit", "test_gen", "custom"):
        return {"error": "نوع مهمة غير صالح"}
    if kind != "custom" and not body.get("path"):
        return {"error": "المسار مطلوب"}
    return orchestrator.new_task(kind, {"path": body.get("path"),
                                        "instruction": body.get("instruction"),
                                        "target": body.get("target")})


@app.get("/api/tasks")
def tasks():
    return {"tasks": orchestrator.all_tasks()}


@app.get("/api/tasks/{tid}")
def task_by(tid: str):
    rec = orchestrator.get_task(tid)
    return rec or {"error": "not found"}


@app.get("/")
@app.get("/dashboard")
def dashboard():
    f = _dsh / "index.html"
    if f.exists():
        return fastapi.Response(f.read_bytes(), media_type="text/html")
    return {"error": "missing dashboard"}


def run(host, port):
    uvicorn.run(app, host=host, port=port, log_level="info")
