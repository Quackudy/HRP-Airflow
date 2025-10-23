from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Portfolio
from ..schemas import PortfolioCreate, PortfolioOut, PortfolioUpdate


router = APIRouter()


@router.post("/", response_model=PortfolioOut)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = Portfolio(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
        stock_tickers=payload.stock_tickers,
        objective_function=payload.objective_function,
        rebalance_interval=payload.rebalance_interval,
        next_optimize_at=payload.next_optimize_at or datetime.now(timezone.utc),
    )
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/", response_model=List[PortfolioOut])
def list_portfolios(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Portfolio).filter(Portfolio.user_id == user.id).all()


@router.get("/{portfolio_id}", response_model=PortfolioOut)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    return portfolio


@router.put("/{portfolio_id}", response_model=PortfolioOut)
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(portfolio, field, value)
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=204)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Portfolio not found")
    db.delete(portfolio)
    db.commit()
    return None


