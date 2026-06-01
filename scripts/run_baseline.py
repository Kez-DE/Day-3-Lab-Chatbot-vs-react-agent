import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chatbot import baseline_chatbot_response


def main():
    query = "Evaluate academic performance for student ID card 822067."
    result = baseline_chatbot_response(query)
    print(result["answer"])


if __name__ == "__main__":
    main()
