import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://nothrovo@127.0.0.1:5432/abuseip")
REMOTE_DATABASE_URL = os.getenv("REMOTE_DATABASE_URL", os.getenv("INTEL_DATABASE_URL", "postgresql://nothrovo@192.168.1.50:5432/abuseip"))
ACTIVE_DB_PROFILE = os.getenv("ACTIVE_DB_PROFILE", "local")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")

# Security and Privacy
ENABLE_LOCAL_AI = os.getenv("ENABLE_LOCAL_AI", "false").lower() in ("true", "1", "yes")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
