import io
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Portfolio, PortfolioWeights, DailyPrice
from ..schemas import ReportMetrics


router = APIRouter()


def _get_latest_weights(db: Session, portfolio_id: int) -> PortfolioWeights:
    return (
        db.query(PortfolioWeights)
        .filter(PortfolioWeights.portfolio_id == portfolio_id)
        .order_by(PortfolioWeights.calculation_date.desc())
        .first()
    )


def _prices_df(db: Session, tickers: List[str]) -> pd.DataFrame:
    q = (
        db.query(DailyPrice)
        .filter(DailyPrice.ticker.in_(tickers))
        .order_by(DailyPrice.date.asc())
    )
    rows = q.all()
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame([
        {
            "ticker": r.ticker,
            "date": r.date,
            "close": r.adj_close if r.adj_close is not None else r.close,
        }
        for r in rows
    ])
    pivot = df.pivot(index="date", columns="ticker", values="close").dropna(how="all")
    return pivot


@router.get("/{portfolio_id}/report", response_model=ReportMetrics)
def report_metrics(portfolio_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    weights_row = _get_latest_weights(db, portfolio_id)
    if not weights_row:
        raise HTTPException(status_code=404, detail="No weights available")
    tickers = list(weights_row.weights.keys())
    prices = _prices_df(db, tickers)
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data")

    # Compute metrics using log returns and simple approximations if quantstats not available
    returns = prices.pct_change().dropna()
    portfolio_returns = (returns * pd.Series(weights_row.weights)).sum(axis=1)
    sharpe = portfolio_returns.mean() / portfolio_returns.std() * (252 ** 0.5) if portfolio_returns.std() != 0 else 0.0
    cum = (1 + portfolio_returns).cumprod()
    peak = cum.cummax()
    drawdown = (cum - peak) / peak
    max_dd = drawdown.min() if not drawdown.empty else 0.0
    days = (prices.index[-1] - prices.index[0]).days or 1
    cagr = (cum.iloc[-1]) ** (365.0 / days) - 1.0

    return ReportMetrics(sharpe=float(sharpe), max_drawdown=float(max_dd), cagr=float(cagr))


@router.get("/{portfolio_id}/report/html", response_class=HTMLResponse)
def report_html(portfolio_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    portfolio = db.query(Portfolio).filter(Portfolio.id == portfolio_id, Portfolio.user_id == user.id).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    weights_row = _get_latest_weights(db, portfolio_id)
    if not weights_row:
        raise HTTPException(status_code=404, detail="No weights available")
    tickers = list(weights_row.weights.keys())
    prices = _prices_df(db, tickers)
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data")

    try:
        import quantstats as qs  # type: ignore

        returns = prices.pct_change().dropna()
        portfolio_returns = (returns * pd.Series(weights_row.weights)).sum(axis=1)
        buf = io.StringIO()
        qs.reports.html(portfolio_returns, title=f"Portfolio {portfolio.id}", output=buf, download_filename=None)
        html = buf.getvalue()
    except Exception:
        html = "<html><body><h1>Report</h1><p>quantstats not available.</p></body></html>"

    return HTMLResponse(content=html)


