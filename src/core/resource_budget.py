"""Resource budget grants for governed Agent-Matrix execution.

This is intentionally independent of blockchain/credit rails. Treasury can expose
those as optional settlement mechanisms; the cognition loop only needs bounded
resources and a hard stop.
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ResourcePolicy:
    max_mxu: float = float(os.getenv("MATRIX_BUDGET_MAX_MXU", "100"))
    max_tokens: int = int(os.getenv("MATRIX_BUDGET_MAX_TOKENS", "100000"))
    max_runtime_seconds: int = int(os.getenv("MATRIX_BUDGET_MAX_RUNTIME_SECONDS", "3600"))
    max_tool_calls: int = int(os.getenv("MATRIX_BUDGET_MAX_TOOL_CALLS", "100"))


def _requested(plan: Dict[str, Any]) -> Dict[str, float]:
    mxu = tokens = runtime = calls = 0.0
    for step in plan.get("steps") or []:
        estimate = step.get("estimated_cost") or {}
        mxu += float(estimate.get("mxu", 1.0))
        tokens += float(estimate.get("tokens", 2000))
        runtime += float(estimate.get("runtime_seconds", 60))
        calls += float(estimate.get("tool_calls", 1))
    return {
        "mxu": mxu,
        "tokens": tokens,
        "runtime_seconds": runtime,
        "tool_calls": calls,
    }


def grant_budget(plan: Dict[str, Any], policy: ResourcePolicy | None = None) -> Dict[str, Any]:
    policy = policy or ResourcePolicy()
    plan_id = str(plan.get("plan_id") or "")
    if not plan_id:
        raise ValueError("plan_id is required")
    req = _requested(plan)

    # Grant is always bounded by the operator's ceiling. hard_stop means runtime
    # MUST terminate rather than silently exceed any granted dimension.
    granted_mxu = min(req["mxu"], policy.max_mxu)
    granted_tokens = min(int(req["tokens"]), policy.max_tokens)
    granted_runtime = min(int(req["runtime_seconds"]), policy.max_runtime_seconds)
    granted_calls = min(int(req["tool_calls"]), policy.max_tool_calls)

    constrained = (
        req["mxu"] > policy.max_mxu
        or req["tokens"] > policy.max_tokens
        or req["runtime_seconds"] > policy.max_runtime_seconds
        or req["tool_calls"] > policy.max_tool_calls
    )
    seed = f"{plan_id}|{time.time_ns()}|{granted_mxu}|{granted_tokens}|{granted_runtime}|{granted_calls}"
    return {
        "grant_id": "bg_" + hashlib.sha256(seed.encode()).hexdigest()[:20],
        "plan_id": plan_id,
        "max_mxu": granted_mxu,
        "max_tokens": granted_tokens,
        "max_runtime_seconds": granted_runtime,
        "hard_stop": True,
        "limits": {
            "max_tool_calls": granted_calls,
            "constrained_by_policy": constrained,
            "requested": req,
        },
    }
