"""
config.py — Central configuration for Nifty100 project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base paths
    BASE_DIR   = Path(__file__).parent.parent.parent
    DB_PATH    = BASE_DIR / "db" / "nifty100.db"
    OUTPUT_DIR = BASE_DIR / "output"
    DATA_DIR   = BASE_DIR / "data"
    LOGS_DIR   = BASE_DIR / "logs"

    def ensure_dirs(self):
        """Create all required directories if they don't exist."""
        for d in [self.OUTPUT_DIR, self.LOGS_DIR, self.DB_PATH.parent]:
            d.mkdir(parents=True, exist_ok=True)


cfg = Config()