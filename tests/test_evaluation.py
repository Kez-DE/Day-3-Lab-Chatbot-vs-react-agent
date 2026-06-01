from scripts.run_evaluation import run_evaluation


def test_run_evaluation_creates_summary_with_agent_successes():
    result = run_evaluation()

    assert result["case_count"] == 4
    assert result["agent_success_count"] == 4
    assert result["baseline_success_count"] == 4
