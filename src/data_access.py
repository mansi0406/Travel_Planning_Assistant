# src/data_access.py

import json
import os
from functools import lru_cache
from typing import Dict, Any

# Project root = one level above src/
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


@lru_cache(maxsize=1)
def load_all_json() -> Dict[str, Any]:
    """
    Load ALL .json files from /data directory once and cache them.

    Returns:
    {
        "flights": [...],
        "hotels": [...],
        "places": [...],
        ...
    }
    """
    data: Dict[str, Any] = {}

    if not os.path.exists(DATA_DIR):
        return data

    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(DATA_DIR, filename)
        key = os.path.splitext(filename)[0]  # flights.json -> flights

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data[key] = json.load(f)
        except Exception as e:
            # Fail-safe: never crash the app
            data[key] = []

    return data
