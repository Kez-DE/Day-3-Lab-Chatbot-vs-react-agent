import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.demo_provider import build_demo_agent


def main():
    agent = build_demo_agent()
    answer = agent.run(
        "Evaluate academic performance for student_id 30 name Royce Lowe id_card 822067."
    )
    print(answer)


if __name__ == "__main__":
    main()
