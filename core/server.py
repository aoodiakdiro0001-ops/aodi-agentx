#!/usr/bin/env python3
"""Aodı-AgentX — core API server (stdlib-first; ويوجد غلاف FastAPI اختياري في app_fastapi.py).

نقاط الواجهة:
  GET  /api/health        فحص كل العقد (متوازٍ)
  POST /api/nodes         إضافة عقدة  {name,url,model?,tags?}
  POST /api/nodes/remove  إزالة      {name}
  GET  /api/nodes         سجل العقد
  POST /api/tasks         إرسال مهمة {kind: code_audit|test_gen|custom, path, instruction?, target?}
  GET  /api/tasks         آخر المهام
  GET  /api/tasks/<id>    حالة/نتيجة مهمة
  GET  /dashboard         لاحقة ثابتة (index.html)
"""
import json, os, sys, argparse, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

CORE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CORE_DIR)
import config
import ollama_client
import orchestrator

STATIC_DIR = Path(__file__).resolve().parent.parent / "dashboard"


class Handler(BaseHTTPRequestHandler):
    server_version = f"AodixCore/{config.VERSION}"

    # ------------------------------------------------------------------ utils
    def _json(self, code, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def log_message(self, fmt, *args):  # هدوء إجباري في اللوج المستخدم
        print(f"[*] {self.client_address[0]} {args[0] % args[1:]}" if args else "",
              flush=True) if False else None

    # ------------------------------------------------------------------ routes
    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            return self._json(200, {"brand": config.BRAND, "version": config.VERSION,
                                    "nodes": ollama_client.health()})
        if path == "/api/nodes":
            return self._json(200, {"nodes": config.load_nodes()})
        if path.startswith("/api/tasks/"):
            tid = path.rsplit("/", 1)[1]
            rec = orchestrator.get_task(tid)
            return self._json(200 if rec else 404, rec or {"error": "not found"})
        if path == "/api/tasks":
            return self._json(200, {"tasks": orchestrator.all_tasks()})
        if path.startswith("/dashboard") or path == "/":
            fname = "index.html"
            f = STATIC_DIR / fname
            if f.exists():
                raw = f.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            return self._json(404, {"error": "missing dashboard/index.html"})
        return self._json(404, {"error": "no route"})

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        body = self._body()
        if path == "/api/nodes":
            name, url = (body.get("name") or "").strip(), (body.get("url") or "").strip()
            if not name or not url:
                return self._json(400, {"error": "name و url مطلوبان"})
            probe = ollama_client.ping_node(url)
            if not probe["ok"]:
                return self._json(400, {"error": "الرابط لا يرد", "probe": probe["error"]})
            nodes = config.load_nodes()
            nodes = [n for n in nodes if n.get("name") != name]
            nodes.append({"name": name, "url": url, "model": body.get("model") or None,
                          "tags": body.get("tags", [])})
            config.save_nodes(nodes)
            return self._json(200, {"ok": True, "nodes": nodes, "probe": probe})
        if path == "/api/nodes/remove":
            nodes = [n for n in config.load_nodes() if n.get("name") != body.get("name")]
            config.save_nodes(nodes)
            return self._json(200, {"ok": True, "nodes": nodes})
        if path == "/api/tasks":
            kind = body.get("kind") or "custom"
            if kind not in ("code_audit", "test_gen", "custom"):
                return self._json(400, {"error": "نوع مهمة غير صالح"})
            if kind != "custom" and not body.get("path"):
                return self._json(400, {"error": "المسار مطلوب لهذا النوع"})
            rec = orchestrator.new_task(kind, {"path": body.get("path"),
                                               "instruction": body.get("instruction"),
                                               "target": body.get("target")})
            return self._json(202, rec)
        return self._json(404, {"error": "no route"})


def _serve(host, port):
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(config.banner(), flush=True)
    print(f"[core] listening on http://{host}:{port}  (AODIX_HOME={config.HOME})", flush=True)
    httpd.serve_forever()


def _fastapi_available():
    try:
        import fastapi  # noqa
        import uvicorn  # noqa
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(prog="agentx-core")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=config.DEFAULT_PORT)
    ap.add_argument("--engine", choices=["auto", "stdlib", "fastapi"], default="auto")
    args = ap.parse_args()
    if args.engine in ("auto", "fastapi") and _fastapi_available():
        try:
            import app_fastapi
            app_fastapi.run(args.host, args.port)
            return
        except Exception as e:
            print(f"[core]FastAPI فشل ({e}) — أعود إلى stdlib", flush=True)
    _serve(args.host, args.port)


if __name__ == "__main__":
    main()
