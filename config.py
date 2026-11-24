"""Configuration module for MobileInfoga.

Loads credentials from environment variables (with optional .env file support).
Never commit real credentials — keep them in a .env file that is git-ignored.
"""

import os
from typing import Optional

# Optional python-dotenv support: load .env if it exists.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def _get_env_int(name: str, default: int = 0) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


API_HASH: str = _get_env("API_HASH", "")
API_ID: int = _get_env_int("API_ID", 0)
PHONE: str = _get_env("PHONE", "")


def validate_credentials() -> Optional[str]:
    """Return an error message if credentials are missing, otherwise None."""
    missing = []
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not PHONE:
        missing.append("PHONE")
    if missing:
        return (
            "Missing required environment variables: "
            + ", ".join(missing)
            + ". Copy .env.example to .env and fill in your credentials."
        )
    return None