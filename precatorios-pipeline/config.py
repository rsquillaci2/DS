"""Configuração central do pipeline de precatórios."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DUCKDB_PATH = DATA_DIR / os.getenv("DUCKDB_PATH", "precatorios.duckdb")

# === API Keys ===
DATAJUD_API_KEY = os.getenv("DATAJUD_API_KEY", "")

# === Rate Limits (req/min) ===
RATE_LIMITS = {
    "datajud": int(os.getenv("DATAJUD_RATE_LIMIT", "30")),
    "djen": int(os.getenv("DJEN_RATE_LIMIT", "60")),
    "cvm": int(os.getenv("CVM_RATE_LIMIT", "60")),
    "sof": int(os.getenv("SOF_RATE_LIMIT", "60")),
}

# === Logging ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
