import os
from dotenv import load_dotenv

load_dotenv()  # loads .env if present

def get_env(name: str, default=None, required: bool = False):
    val = os.getenv(name, default)
    if required and (val is None or str(val).strip() == ""):
        raise RuntimeError(f"Missing required env var: {name}")
    return val

INVENTISION_USER = get_env("INVENTISION_USER", required=True)
INVENTISION_PASS = get_env("INVENTISION_PASS", required=True)
INVENTISION_IP   = get_env("INVENTISION_IP", required=True)

INVENTISION_PORT    = int(get_env("INVENTISION_PORT", "554"))
INVENTISION_CHANNEL = int(get_env("INVENTISION_CHANNEL", "1"))
INVENTISION_SUBTYPE = int(get_env("INVENTISION_SUBTYPE", "0"))
