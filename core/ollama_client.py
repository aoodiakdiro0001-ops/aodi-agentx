"""Aodı-AgentX — multi-node Ollama client with failover + parallel dispatch (stdlib-only)."""
import json, time, urllib.request, urllib.error, threading
from concurrent.futures import ThreadPoolExecutor

import config

_ctx_lock = threading.Lock()
_health_cache = {}   # url -> {"ok":bool,"latency_ms":int,"models":[...],"error":str}


def _req(method, url, payload=None, timeout=60):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ping_node(url):
    """يعدل _health_cache ويولّد سجل صحة العقدة."""
    t0 = time.time()
    entry = {"ok": False, "latency_ms": None, "models": [], "error": None}
    try:
        tags = _req("GET", url.rstrip("/") + "/api/tags", timeout=8)
        entry["ok"] = True
        entry["latency_ms"] = int((time.time() - t0) * 1000)
        entry["models"] = [m.get("name", "?") for m in tags.get("models", [])]
    except Exception as e:  # شاملة: URLError/HTTPError/Common
        entry["error"] = f"{type(e).__name__}: {e}"[:160]
    with _ctx_lock:
        _health_cache[url] = entry
    return entry


def health(nodes=None):
    """فحص متواز لكل العقد."""
    nodes = nodes or config.load_nodes()
    urls = [n.get("url", "") for n in nodes if n.get("url")]
    if urls:
        with ThreadPoolExecutor(max_workers=min(8, len(urls))) as ex:
            list(ex.map(ping_node, urls))
    out = []
    for n in nodes:
        h = _health_cache.get(n.get("url"), {"ok": False, "latency_ms": None,
                                            "models": [], "error": "never-pinged"})
        out.append({"name": n.get("name"), "url": n.get("url"), "model": n.get("model"),
                    "tags": n.get("tags", []), **{k: h[k] for k in
                    ("ok", "latency_ms", "models", "error")}})
    return out


def pick_nodes(nodes=None, virt_filter=None):
    """يرتب العقد الصحيحة أولاً (كالجولة بينها عند تكرار الدفوع)."""
    nodes = nodes if nodes is not None else config.load_nodes()
    alive = [n for n in nodes if _health_cache.get(n.get("url"), {}).get("ok")]
    if not alive:
        return nodes if not virt_filter else [n for n in nodes if virt_filter(n)]
    if virt_filter:
        hs = [n for n in alive if virt_filter(n)]
        return hs or alive
    return alive


def generate(nodes, system, prompt, timeout=None, temperature=0.25,
             expect_json=False, parallel_chunk=False):
    """طلب واحد عبر أول عقدة صحيحة مع فشل سلس إلى الأخرى.
    يعيد dict: {ok, text, node, model, latency_ms, error}."""
    timeout = timeout or config.DEFAULT_TIMEOUT
    last_err, tried = None, []
    pool = pick_nodes(nodes)
    for n in pool:
        url = n["url"].rstrip("/")
        payload = {
            "model": n.get("model") or _first_model(url),
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": 8192},
        }
        if not payload["model"]:
            last_err = f"node {n.get('name')}: بلا نموذج"
            tried.append(n.get("name"))
            continue
        try:
            t0 = time.time()
            out = _req("POST", url + "/api/generate", payload, timeout=timeout)
            txt = (out.get("response") or "").strip()
            if expect_json:
                txt = _strip_fences(txt)
            return {"ok": True, "text": txt, "node": n.get("name"),
                    "model": payload["model"],
                    "latency_ms": int((time.time() - t0) * 1000), "error": None}
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"[:180]
            tried.append(n.get("name"))
    return {"ok": False, "text": "", "node": ",".join(map(str, tried)) or "none",
            "model": None, "latency_ms": None, "error": last_err}


def _first_model(url):
    h = _health_cache.get(url)
    if h and h.get("models"):
        return h["models"][0]
    p = ping_node(url)
    return (p.get("models") or [None])[0]


def _strip_fences(s):
    s = s.strip()
    if s.startswith("```"):
        s = s[3:]
        if s.startswith("json"): s = s[4:]
        s = s.strip()
    if s.endswith("```"):
        s = s[:-3].strip()
    return s


def generate_many(nodes, jobs, max_workers=4, temperature=0.25):
    """تشغيل موازي للوكلاء عبر عقد عديدة. jobs: [{node?, system, prompt}].
    يعيد قائمة نتائج بنفس الترتيب."""
    def one(job):
        chosen = [nodes[job["node_idx"]]] if "node_idx" in job else nodes
        return generate(chosen or nodes, job.get("system", ""), job["prompt"],
                        temperature=job.get("temperature", temperature),
                        expect_json=job.get("expect_json", False))
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        return list(ex.map(one, jobs))
