"""Central settings. Other modules read these at call time (cfg.X), so the
notebook can change e.g. cfg.OFFLINE = True and every module sees it."""
import os
import datetime as dt
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

NPS_API_KEY = os.getenv("NPS_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

NPS_BASE = "https://developer.nps.gov/api/v1"
CACHE_DIR = Path(os.getenv("PARKCHECK_CACHE", "nps_cache"))
RESULTS_DIR = Path("results")

# All three configs read the same snapshot. Freeze it for the evaluation run.
SNAPSHOT_DATE = os.getenv("SNAPSHOT_DATE", dt.date.today().isoformat())
# When True, the NPS client never hits the network and only reads the cache.
OFFLINE = os.getenv("PARKCHECK_OFFLINE", "0") == "1"

# ---- Models (pin exact strings here and in the README) ----------------------
# A and B share the mid-tier model; C is the small model. One provider only.
MODEL_MID = "gpt-5.6-terra"
MODEL_SMALL = "gpt-5.6-luna"

# USD per 1M tokens (input, output). Check these against the OpenAI pricing
# page on the day you run the evaluation; Luna's price was cut after launch.
PRICES_PER_1M = {
    MODEL_MID: (2.00, 12.00),
    MODEL_SMALL: (0.20, 1.20),
}

TEMPERATURE = 0.0
MAX_STEPS = 5              # max model calls per query in the tool loop
MAX_TOOL_CHARS = 20000     # hard cap on one tool result sent to the model
