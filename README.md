# Lab 3: Chatbot vs ReAct Agent

This repo implements a small academic advising agent for comparing a simple chatbot baseline with a ReAct-style agent.

The agent evaluates student performance from `Data/database.csv` by validating a student, reading marks, calculating the average score, checking failed courses, and assigning an academic category.

## Dataset

`Data/database.csv` contains 100 student records with these columns:

- `ID`
- `Name`
- `ID_Card`
- `Computer Science`
- `Microeconomics`
- `Data Structures and Algorithms`
- `Calculus`
- `Linear Algebra`

Scores use comma decimals in the CSV, for example `9,30`. The Python tools convert them to floats before calculation.

The dataset has no explicit semester or student-status column. In this lab, it is treated as one score snapshot for demonstration.

## Lab Objectives

1. **Baseline Chatbot**: provide a simple non-ReAct comparison point.
2. **ReAct Loop**: implement `Thought → Action → Observation → Final Answer` in `src/agent/agent.py`.
3. **Provider Switching**: keep the agent behind the `LLMProvider` interface so OpenAI, Gemini, local models, or the deterministic demo provider can be used.
4. **Failure Analysis**: use logs in `logs/` to inspect tool calls, parser errors, and final answers.
5. **Evaluation and Report**: compare baseline vs agent and write group/individual reports.

## Project Structure

```text
Data/database.csv                         # score dataset
src/agent/agent.py                        # ReAct loop
src/chatbot.py                            # baseline chatbot
src/demo_provider.py                      # deterministic offline provider
src/tools/score_tools.py                  # score analysis tools
src/core/*.py                             # provider interface and model providers
src/telemetry/*.py                        # JSON logs and metrics
scripts/run_baseline.py                   # baseline demo
scripts/run_demo_agent.py                 # ReAct demo
scripts/run_evaluation.py                 # benchmark runner
evaluation/results.json                   # generated evaluation result
evaluation/summary.md                     # generated evaluation summary
report/group_report/GROUP_REPORT_NHOM_F2.md
report/individual_reports/REPORT_NGUYEN_DUC_KHANG_2A202600588.md
tests/                                    # automated tests
```

## Setup

Create or activate the virtual environment, then install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

If `.venv` already exists, use it directly:

```bash
. .venv/bin/activate
```

## Running Tests

```bash
.venv/bin/python -m pytest -q
```

Latest verified result:

```text
15 passed
```

## Running the Baseline

```bash
.venv/bin/python scripts/run_baseline.py
```

The baseline extracts a student identifier and returns a direct academic summary. It does not expose a ReAct trace.

## Running the ReAct Demo Agent

```bash
.venv/bin/python scripts/run_demo_agent.py
```

The demo provider is deterministic and does not require an API key. It follows the same ReAct format expected from a real LLM provider.

Example flow:

```text
Thought: validate the student
Action: validate_student(30, "Royce Lowe", "822067")
Observation: Royce Lowe found

Thought: evaluate marks and category
Action: categorize_academic_performance(822067)
Observation: average_score = 8.39, category = Giỏi

Final Answer: Royce Lowe has average score 8.39 and academic category Giỏi.
```

## Running Evaluation

```bash
.venv/bin/python scripts/run_evaluation.py
```

This writes:

```text
evaluation/results.json
evaluation/summary.md
```

Current benchmark:

- Royce Lowe / 822067 → Giỏi
- Emmanuel Myers / 107226 → Khá
- Axl Waters / 876012 → Trung bình with failed course
- Invalid ID / 999999 → not found

Latest verified result:

```text
Baseline success: 4/4
Agent success: 4/4
```

## Academic Policy Used

Pass threshold:

```text
course score >= 4.0
```

Academic category by average score on a 10-point scale:

- Xuất sắc: average_score >= 9.0
- Giỏi: 8.0 <= average_score < 9.0
- Khá: 6.5 <= average_score < 8.0
- Trung bình: 5.0 <= average_score < 6.5
- Yếu: average_score < 5.0

Additional rule:

```text
To be categorized as Khá or above, the student must pass every course.
```

## Reports

Group report:

```text
report/group_report/GROUP_REPORT_NHOM_F2.md
```

Individual report for Nguyễn Đức Khang:

```text
report/individual_reports/REPORT_NGUYEN_DUC_KHANG_2A202600588.md
```

## Local Model Option

The repo still supports local GGUF models through `src/core/local_provider.py`. To use a local model, download a GGUF model and set:

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

Model files should stay under `models/` and should not be committed.

## Notes

- `.env` is ignored and should not be committed.
- `logs/` is ignored because it is generated during runs.
- `evaluation/` contains generated benchmark artifacts used by the reports.
