"""
database.py — Data access layer for student records.
Loads the CSV once at import time; all lookups are in-memory.
"""

import csv
import os
from pathlib import Path
from typing import Optional

# ── path resolution ──────────────────────────────────────────────────────────
_BASE_DIR = Path(__file__).resolve().parents[2]
_CSV_PATH = _BASE_DIR / "data" / "database.csv"

SUBJECTS = [
    "Computer Science",
    "Microeconomics",
    "Data Structures and Algorithms",
    "Calculus",
    "Linear Algebra",
]

# ── loader ───────────────────────────────────────────────────────────────────

def _parse_score(raw: str) -> float:
    """Handle European decimal separator (comma → dot)."""
    return float(raw.strip().replace(",", "."))


def _load_database() -> list[dict]:
    records = []
    with open(_CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            try:
                record = {
                    "id":      int(row["ID"]),
                    "name":    row["Name"].strip(),
                    "id_card": str(row["ID_Card"]).strip(),
                    "scores": {
                        subj: _parse_score(row[subj]) for subj in SUBJECTS
                    },
                }
                records.append(record)
            except (ValueError, KeyError):
                continue   # skip malformed rows silently
    return records


_DB: list[dict] = _load_database()

# ── public lookup helpers ─────────────────────────────────────────────────────

def find_by_id(student_id: str) -> Optional[dict]:
    sid = str(student_id).strip()
    return next((r for r in _DB if str(r["id"]) == sid), None)


def find_by_name(name: str) -> Optional[dict]:
    target = name.strip().lower()
    return next((r for r in _DB if r["name"].lower() == target), None)


def find_by_id_card(id_card: str) -> Optional[dict]:
    return next((r for r in _DB if r["id_card"] == str(id_card).strip()), None)


def get_all() -> list[dict]:
    return _DB
