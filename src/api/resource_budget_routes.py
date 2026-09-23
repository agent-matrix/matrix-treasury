from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.resource_budget import grant_budget

router = APIRouter(prefix="/v1", tags=["Resource Budget"])


class BudgetGrantRequest(BaseModel):
    plan: Dict[str, Any]


@router.post("/budget/grant")
def budget_grant(req: BudgetGrantRequest) -> Dict[str, Any]:
    try:
        return grant_budget(req.plan)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
