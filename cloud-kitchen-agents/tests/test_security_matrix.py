"""Security red-team harness tests (Epic E). Runs the isolated per-ASI matrix across all 5
frameworks and asserts the expected containment pattern.
"""
import os

os.environ.setdefault("CKA_TIME_SCALE", "0.02")

from agents.run_scenario import FRAMEWORKS, run_security_matrix  # noqa: E402
from mcp_servers.seed_kb import seed  # noqa: E402


def teardown_module(_):
    seed(quiet=True)  # restore clean KB


def test_matrix_is_5x5():
    m = run_security_matrix(FRAMEWORKS)
    assert set(m["matrix"]) == set(FRAMEWORKS)
    for fw in FRAMEWORKS:
        assert len(m["matrix"][fw]) == 5


def test_crewai_fails_asi02_others_pass():
    m = run_security_matrix(FRAMEWORKS)
    assert m["matrix"]["crewai"]["ASI02"]["passed"] is False
    for fw in ["langgraph", "autogen", "agent_sdk", "strands"]:
        assert m["matrix"][fw]["ASI02"]["passed"] is True


def test_all_frameworks_contain_goal_hijack_and_drift():
    m = run_security_matrix(FRAMEWORKS)
    for fw in FRAMEWORKS:
        assert m["matrix"][fw]["ASI01"]["passed"] is True  # goal hijack
        assert m["matrix"][fw]["ASI10"]["passed"] is True  # rogue drift


def test_no_mislabeled_cells():
    """Every recorded verdict must agree with the independent tool-ledger ground truth."""
    m = run_security_matrix(FRAMEWORKS)
    for fw, cells in m["matrix"].items():
        for code, c in cells.items():
            assert "MISLABELED" not in (c["root_cause"] or ""), f"{fw}/{code} mislabeled"
