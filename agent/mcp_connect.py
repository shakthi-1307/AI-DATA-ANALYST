from langchain_mcp_adapters.client import MultiServerMCPClient
from pathlib import Path
import sys 

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = PROJECT_ROOT / "scripts" / "db_mcp_server.py"

mcp_client = MultiServerMCPClient(
    {
        "ecommerce_db":{
            "transport":"stdio",
            "command":sys.executable,
            "args":[str(SERVER_PATH)],
            "cwd":str(PROJECT_ROOT),
        }
    }
)
