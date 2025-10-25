from datetime import datetime
from typing import List, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    name: str
    description: Optional[str] = None
    stock_tickers: List[str]
    objective_function: str
    rebalance_interval: str
    period: str
    next_optimize_at: Optional[datetime] = None


class PortfolioCreate(PortfolioBase):
    pass


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    stock_tickers: Optional[List[str]] = None
    objective_function: Optional[str] = None
    rebalance_interval: Optional[str] = None
    next_optimize_at: Optional[datetime] = None


class PortfolioOut(PortfolioBase):
    id: int
    user_id: int
    last_optimized_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReportMetrics(BaseModel):
    sharpe: float
    max_drawdown: float
    cagr: float
    weights: Dict[str, float]
    


class PortfolioWeightsOut(BaseModel):
    id: int
    portfolio_id: int
    calculation_date: datetime
    weights: Dict[str, float]

    class Config:
        from_attributes = True


