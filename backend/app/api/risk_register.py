from typing import List
from fastapi import APIRouter
from backend.app.models.schemas import RiskItem
from backend.app.database.db import execute_query

router = APIRouter(prefix="/risk-register", tags=["risk-register"])

@router.get("", response_model=List[RiskItem])
async def get_risk_register():
    rows = execute_query(
        "SELECT id, risk, category, status, mitigation, test_coverage FROM risk_register"
    )
    return [RiskItem(**r) for r in rows]
