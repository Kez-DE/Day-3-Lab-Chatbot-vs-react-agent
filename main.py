"""
main.py — Run all evaluation scenarios from SCORING.md

Cases:
  1. Royce Lowe      → Giỏi
  2. Emmanuel Myers  → Khá
  3. Invalid ID      → Error handling
  4. Failed-course student (Kiara Perkins, score CS=3.82)
"""

from src.agent.agent import run_agent

DIVIDER = "\n" + "█" * 60 + "\n"


def run_case(title: str, **kwargs):
    print(f"{DIVIDER}▶ {title}{DIVIDER}")
    result = run_agent(**kwargs)
    print(result)


if __name__ == "__main__":

    # Case 1 — Royce Lowe (ID=30) — Expected: Giỏi
    run_case("Case 1: Royce Lowe — Expected Giỏi",
             student_name="Royce Lowe", semester="Spring 2026")

    # Case 2 — Emmanuel Myers (ID=4) — Expected: Khá
    run_case("Case 2: Emmanuel Myers — Expected Khá",
             student_name="Emmanuel Myers", semester="Spring 2026")

    # Case 3 — Invalid student ID
    run_case("Case 3: Invalid ID — Expected error",
             student_id="9999", semester="Spring 2026")

    # Case 4 — Kiara Perkins (ID=1) — CS=3.82 → failed subject → demotion
    run_case("Case 4: Kiara Perkins — Failed subject, demotion test",
             student_id="1", semester="Spring 2026")

    # Case 5 — Lookup by ID_Card
    run_case("Case 5: Lookup by ID_Card (Sara Richards, card=397793)",
             id_card="397793", semester="Spring 2026")
