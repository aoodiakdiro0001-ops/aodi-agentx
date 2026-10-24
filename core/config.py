"""Aodı-AgentX 1.0.0 — core config & local state (stdlib-only)."""
import json, os
from pathlib import Path

VERSION = "1.0.0"
BRAND = "Aodı-AgentX"

HOME = Path(os.environ.get("AODIX_HOME", str(Path.home() / ".aodix")))
HOME.mkdir(parents=True, exist_ok=True)
NODES_FILE = HOME / "nodes.json"
TASKS_LOG = HOME / "tasks.jsonl"

DEFAULT_TIMEOUT = int(os.environ.get("AODX_TIMEOUT", "180"))
DEFAULT_PORT = int(os.environ.get("AODX_PORT", "8787"))
MAX_FILE_BYTES = 100_000
SCAN_EXTS = (".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java", ".json",
             ".sh", ".md", ".sql", ".yaml", ".yml", ".sol")
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist",
             "build", ".next", ".cache", ".github"}
BATCH_CHARS = 3500


def load_nodes():
    """[{name,url,model,tags}] من AODIX_HOME/nodes.json."""
    if NODES_FILE.exists():
        try:
            return json.loads(NODES_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def save_nodes(nodes):
    NODES_FILE.write_text(json.dumps(nodes, ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")


def log_task(record):
    with open(TASKS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def banner():
    lines = [
        "===============================================",
        f"  {BRAND} v{VERSION} — distributed AI operator",
        "  core server: api.health / nodes / tasks / report",
        "===============================================",
    ]
    return "\n".join(lines)
