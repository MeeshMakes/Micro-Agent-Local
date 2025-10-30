from subprocess import run
from pathlib import Path
STORE = Path(__file__).resolve().parents[2]/"agent_macros"/"store.jsonl"
MANAGER = Path("/path/to/system_tools/system_macros/manager.py")

def add_macro(body, shell="powershell", macro_id=None, tags=None):
    cmd = ["python", str(MANAGER), str(STORE), "add", body]
    if macro_id: cmd += ["--id", macro_id]
    if shell: cmd += ["--shell", shell]
    if tags: cmd += ["--tags", ",".join(tags)]
    run(cmd, check=True)
