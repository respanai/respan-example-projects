import os
from dotenv import load_dotenv

load_dotenv(override=True)

RESPAN_BASE_URL = os.getenv("RESPAN_BASE_URL")
RESPAN_API_KEY = os.getenv("RESPAN_API_KEY")
RESPAN_BASE_HEADERS = {
    "Authorization": f"Bearer {RESPAN_API_KEY}",
    "Content-Type": "application/json",
}

# Every agent run tags its logs with this metadata key, so they can be listed
# later with the `metadata__eval_run` filter.
EVAL_RUN_METADATA_KEY = "eval_run"
EVAL_RUN_ID = "traveling_agent_eval"
EVAL_RUN_FILTER_KEY = f"metadata__{EVAL_RUN_METADATA_KEY}"
