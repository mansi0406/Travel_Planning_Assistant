# tests/conftest.py
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest

# ---------------------------------------------------------------------
# Project root + PYTHONPATH setup (fixes: ModuleNotFoundError: src, etc.)
# ---------------------------------------------------------------------
def _project_root() -> Path:
    """
    Returns the project root directory:
    <project_root>/tests/conftest.py  -> parents[1] is <project_root>
    """
    return Path(__file__).resolve().parents[1]


def pytest_configure():
    """
    Called once by pytest before collecting tests.

    Ensures:
    - project root is on sys.path so `import src...` works
    - cwd is set to project root so relative paths like `data/...` work
    """
    root = _project_root()

    # Add project root to Python path
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    # Set current working directory to project root (helps relative file paths)
    os.chdir(root)


# ---------------------------------------------------------------------
# Core fixtures used by multiple tests
# ---------------------------------------------------------------------
@pytest.fixture(scope="session")
def root() -> Path:
    """Project root path fixture."""
    return _project_root()


@pytest.fixture(scope="session")
def data_dir(root: Path) -> Path:
    """
    Path to <project_root>/data.
    Skip dependent tests if data folder is missing.
    """
    d = root / "data"
    if not d.exists():
        pytest.skip("data/ folder not found. Skipping JSON data tests.")
    return d


# ---------------------------------------------------------------------
# IMPORTANT: JSON files may be list-root, so return type is Any
# ---------------------------------------------------------------------
@pytest.fixture(scope="session")
def flights_json(data_dir: Path):
    """
    Loads data/flights.json.
    Returns the parsed JSON (often a list of records).
    """
    path = data_dir / "flights.json"
    if not path.exists():
        pytest.skip("data/flights.json not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def hotels_json(data_dir: Path):
    """
    Loads data/hotels.json.
    Returns the parsed JSON (often a list of records).
    """
    path = data_dir / "hotels.json"
    if not path.exists():
        pytest.skip("data/hotels.json not found.")
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def places_json(data_dir: Path):
    """
    Loads data/places.json.
    Returns the parsed JSON (often a list of records).
    """
    path = data_dir / "places.json"
    if not path.exists():
        pytest.skip("data/places.json not found.")
    return json.loads(path.read_text(encoding="utf-8"))
