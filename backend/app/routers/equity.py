from typing import List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.equity_curve import compute_equity_curve


router = APIRouter(prefix="/api/simulations", tags=["模拟交易"])


class OperationIn(BaseModel):
    type: Literal["buy", "sell"]
    stock_code: str
    stock_name: str
    price: float
    quantity: float
    total_amount: float
    timestamp: str  # "YYYY-MM-DD HH:mm:ss"


class EquityPoint(BaseModel):
    date: str  # "YYYY-MM-DD"
    total_assets: float
    cash: float
    market_value: float
    position_quantity: float
    close_price: float
    nav: float


class TradeMarker(BaseModel):
    date: str  # "YYYY-MM-DD" (aligned to points.date)
    type: Literal["buy", "sell"]
    timestamp: str
    stock_code: str
    stock_name: str
    price: float
    quantity: float
    total_amount: float
    total_assets_at_marker: float


class EquityCurveRequest(BaseModel):
    # Backward compatible: old clients send `stock_code`.
    # New clients can send `symbol` + `instrument_type`.
    stock_code: str = Field(..., description="兼容字段：用于旧前端/旧数据结构")
    instrument_type: Literal["etf", "stock", "index"] = Field(
        "etf", description="标的类型：etf/stock/index（指数）"
    )
    initial_capital: float = Field(..., gt=0)
    operations: List[OperationIn]
    adjust: str = "qfq"
    days_back: int = 120  # akshare 容错：覆盖节假日/缺失数据


class EquityCurveResponse(BaseModel):
    stock_code: str
    start_date: str
    end_date: str
    points: List[EquityPoint]
    trade_markers: List[TradeMarker]


@router.post("/equity-curve", response_model=EquityCurveResponse)
def equity_curve(req: EquityCurveRequest) -> EquityCurveResponse:
    return compute_equity_curve(
        stock_code=req.stock_code,
        initial_capital=req.initial_capital,
        operations=req.operations,
        instrument_type=req.instrument_type,
        adjust=req.adjust,
        days_back=req.days_back,
    )

