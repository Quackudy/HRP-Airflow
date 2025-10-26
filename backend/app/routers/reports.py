import io
from datetime import datetime
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db, get_async_db
from ..deps import get_current_user
from ..models import Portfolio, PortfolioWeights, DailyPrice
from ..schemas import ReportMetrics

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_latest_weights(db: AsyncSession, portfolio_id: int) -> PortfolioWeights:
    stmt = (
        select(PortfolioWeights)
        .where(PortfolioWeights.portfolio_id == portfolio_id)
        .order_by(PortfolioWeights.calculation_date.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _prices_df(db: AsyncSession, tickers: List[str]) -> pd.DataFrame:
    stmt = (
        select(DailyPrice)
        .where(DailyPrice.ticker.in_(tickers))
        .order_by(DailyPrice.date.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    
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
async def report_metrics(
    portfolio_id: int, 
    db: AsyncSession = Depends(get_async_db), 
    user=Depends(get_current_user)
):
    stmt = select(Portfolio).where(
        and_(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    weights_row = await _get_latest_weights(db, portfolio_id)
    if not weights_row:
        raise HTTPException(status_code=404, detail="No weights available")
    
    tickers = list(weights_row.weights.keys())
    prices = await _prices_df(db, tickers)
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data")

    returns = prices.pct_change().dropna()
    portfolio_returns = (returns * pd.Series(weights_row.weights)).sum(axis=1)
    sharpe = portfolio_returns.mean() / portfolio_returns.std() * (252 ** 0.5) if portfolio_returns.std() != 0 else 0.0
    cum = (1 + portfolio_returns).cumprod()
    peak = cum.cummax()
    drawdown = (cum - peak) / peak
    max_dd = drawdown.min() if not drawdown.empty else 0.0
    days = (prices.index[-1] - prices.index[0]).days or 1
    cagr = (cum.iloc[-1]) ** (365.0 / days) - 1.0

    return ReportMetrics(
        sharpe=float(sharpe),
        max_drawdown=float(max_dd),
        cagr=float(cagr),
        weights={k: float(v) for k, v in weights_row.weights.items()}
    )


import tempfile
import os

@router.get("/{portfolio_id}/report/html", response_class=HTMLResponse)
async def report_html(
    portfolio_id: int,
    db: AsyncSession = Depends(get_async_db),
    user=Depends(get_current_user)
):
    stmt = select(Portfolio).where(
        and_(Portfolio.id == portfolio_id, Portfolio.user_id == user.id)
    )
    result = await db.execute(stmt)
    portfolio = result.scalar_one_or_none()
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    weights_row = await _get_latest_weights(db, portfolio_id)
    if not weights_row:
        raise HTTPException(status_code=404, detail="No weights available")
    
    tickers = list(weights_row.weights.keys())
    prices = await _prices_df(db, tickers)
    if prices.empty:
        raise HTTPException(status_code=404, detail="No price data")

    try:
        import quantstats as qs 
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        portfolio_returns = (returns * pd.Series(weights_row.weights)).sum(axis=1)
        portfolio_returns.index = pd.to_datetime(portfolio_returns.index)
        portfolio_returns = portfolio_returns[~portfolio_returns.index.duplicated(keep='first')]
        portfolio_returns = portfolio_returns.sort_index()
        
        # Create temporary file for output
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as tmp:
            tmp_path = tmp.name
        
        try:
            # Generate report to temporary file
            qs.reports.html(
                portfolio_returns, 
                title=portfolio.name,
                output=tmp_path,
                download_filename=None
            )
            
            # Read the generated HTML
            with open(tmp_path, 'r', encoding='utf-8') as f:
                html = f.read()
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        style_tag = """
        <style>
            body, div, h1, h2, h3, h4, h5, p, span, li, th, td, table {
                color: white !important;
                background-color: transparent !important;
            }
            /* Keep table borders visible */
            table, th, td {
                border-color: #555 !important;
            }
        </style>
        """
        html = html.replace("</head>", f"{style_tag}</head>", 1)
        
    except Exception as e:
        logger.error(f"QuantStats report generation failed: {e}", exc_info=True)
        html = f"""
        <html>
        <head><title>Portfolio Report Error</title></head>
        <body>
            <h1>Portfolio Report Generation Failed</h1>
            <p>Unable to generate quantstats report.</p>
            <p>Error: {str(e)}</p>
        </body>
        </html>
        """

    return HTMLResponse(content=html)
