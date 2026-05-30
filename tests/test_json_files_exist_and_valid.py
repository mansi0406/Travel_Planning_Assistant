# tests/test_json_files_exist_and_valid.py
from __future__ import annotations

from pathlib import Path


def test_data_folder_exists(data_dir: Path):
    assert data_dir.exists()
    assert data_dir.is_dir()


def test_required_json_files_present(data_dir: Path):
    required = ["flights.json", "hotels.json", "places.json"]
    for f in required:
        assert (data_dir / f).exists(), f"Missing file: data/{f}"
