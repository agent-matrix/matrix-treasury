from src.core.resource_budget import ResourcePolicy, grant_budget


def plan():
    return {
        "plan_id": "p1",
        "steps": [{
            "estimated_cost": {
                "mxu": 25,
                "tokens": 5000,
                "runtime_seconds": 120,
                "tool_calls": 3,
            }
        }],
    }


def test_grant_has_hard_stop():
    g = grant_budget(plan())
    assert g["hard_stop"] is True
    assert g["plan_id"] == "p1"


def test_policy_caps_every_resource():
    p = ResourcePolicy(max_mxu=10, max_tokens=1000, max_runtime_seconds=30, max_tool_calls=1)
    g = grant_budget(plan(), p)
    assert g["max_mxu"] == 10
    assert g["max_tokens"] == 1000
    assert g["max_runtime_seconds"] == 30
    assert g["limits"]["max_tool_calls"] == 1
    assert g["limits"]["constrained_by_policy"] is True
