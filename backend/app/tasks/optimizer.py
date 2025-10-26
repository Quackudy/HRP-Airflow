import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

import pandas as pd
import yfinance as yf

from ..models import Portfolio, PortfolioWeights, DailyPrice

log = logging.getLogger(__name__)


def fetch_and_upsert_prices(session, tickers: List[str], period: str = "1y") -> pd.DataFrame:
    """Download price data for tickers and upsert into daily_prices table.

    Returns a DataFrame indexed by date with columns for each ticker (adj_close if available).
    The session is a SQLAlchemy Session (sync).
    """
    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            threads=True,
        )
    except Exception as e:
        log.exception("yfinance download failed")
        return pd.DataFrame()

    prices: Dict[str, pd.DataFrame] = {}

    # Normalize returned structure into a dict of DataFrames (date + adj_close)
    if isinstance(data.columns, pd.MultiIndex):
        # MultiIndex when group_by='ticker'
        for ticker in tickers:
            if ticker not in data.columns.levels[0]:
                continue
            df = data[ticker].reset_index()
            if "Adj Close" in df.columns:
                df = df[["Date", "Adj Close"]].rename(columns={"Date": "date", "Adj Close": "adj_close"})
            else:
                df = df[["Date", "Close"]].rename(columns={"Date": "date", "Close": "adj_close"})
            df["date"] = pd.to_datetime(df["date"]).dt.date
            prices[ticker] = df
    else:
        # Single ticker or non-grouped
        df = data.reset_index().rename(columns={"Date": "date", "Adj Close": "adj_close", "Close": "close"})
        if len(tickers) == 1:
            ticker = tickers[0]
            if "adj_close" not in df.columns and "close" in df.columns:
                df["adj_close"] = df["close"]
            df = df[["date", "adj_close"]]
            df["date"] = pd.to_datetime(df["date"]).dt.date
            prices[ticker] = df

    # Upsert into DB (simple per-row check). For larger scale consider bulk upsert.
    for ticker, df in prices.items():
        for _, row in df.iterrows():
            date = row["date"]
            adj_close = None
            if "adj_close" in row and pd.notna(row["adj_close"]):
                adj_close = float(row["adj_close"])
            elif "close" in row and pd.notna(row["close"]):
                adj_close = float(row["close"])

            # Try to find existing
            existing = (
                session.query(DailyPrice)
                .filter(DailyPrice.ticker == ticker, DailyPrice.date == date)
                .first()
            )
            if existing:
                # update fields
                existing.adj_close = adj_close
            else:
                dp = DailyPrice(
                    ticker=ticker,
                    date=date,
                    adj_close=adj_close,
                )
                session.add(dp)
        # commit per-ticker to keep transaction size reasonable
        try:
            session.commit()
        except Exception:
            session.rollback()
            log.exception("Failed committing prices for %s", ticker)

    # Build pivot DataFrame to return
    df_list = []
    for ticker, df in prices.items():
        tmp = df.set_index("date")["adj_close"].rename(ticker)
        df_list.append(tmp)
    if not df_list:
        return pd.DataFrame()
    result = pd.concat(df_list, axis=1)
    result.sort_index(inplace=True)
    return result


def run_hrp_for_returns(returns: pd.DataFrame, config: Optional[dict] = None) -> Dict[str, float]:
    """Run riskfolio-lib HRP optimization and return weights mapping ticker->weight.

    `returns` should be a DataFrame of daily returns with tickers as columns.
    """
    config = config or {}
    try:
        import riskfolio as rp

        port = rp.HCPortfolio(returns=returns)
        w = port.optimization(
            model=config.get("model", "HRP"),
            codependence=config.get("codependence", "pearson"),
            rm=config.get("rm", "MV"),
            rf=config.get("rf", 0),
            linkage=config.get("linkage", "single"),
            max_k=config.get("max_k", 10),
            leaf_order=config.get("leaf_order", True),
        )
     
        if hasattr(w, "index"):
            weights = {str(idx): float(w.loc[idx][0]) for idx in w.index}
        else:
            weights = {col: float(w[col].iloc[0]) for col in w.columns}
        return weights
    except Exception:
        log.exception("HRP optimization failed")
        raise


def process_portfolio(session, portfolio_id: int, period: str = "2y") -> dict:
    """High-level orchestration: fetch config, update prices, compute weights, persist weights and schedule.

    Returns a dict summary with success flag and details.
    """
    try:
        portfolio = session.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            return {"success": False, "error": "portfolio_not_found"}

        tickers = portfolio.stock_tickers or []
        if not tickers:
            return {"success": False, "error": "no_tickers"}

        prices = fetch_and_upsert_prices(session, tickers, period=portfolio.period)
        if prices.empty:
            return {"success": False, "error": "no_price_data"}

        returns = prices.pct_change().dropna()
        if returns.empty:
            return {"success": False, "error": "not_enough_returns"}

        weights = run_hrp_for_returns(returns, {"rm": portfolio.objective_function})

        # Persist weights
        pw = PortfolioWeights(
            portfolio_id=portfolio.id,
            calculation_date=datetime.now(timezone.utc),
            weights=weights,
        )
        session.add(pw)

        # Update portfolio schedule: set last_optimized_at and next_optimize_at roughly
        now = datetime.now(timezone.utc)
        portfolio.last_optimized_at = now
        # Simple next schedule: interpret common intervals
        interval = (portfolio.rebalance_interval or "6m").lower()
        if interval in ("6m", "semiannual", "semi-annual"):
            delta = timedelta(days=182)
        elif interval in ("monthly", "1m"):
            delta = timedelta(days=30)
        elif interval in ("quarterly", "3m"):
            delta = timedelta(days=91)
        elif interval in ("weekly", "1w"):
            delta = timedelta(weeks=1)
        else:
            # default: 6 months
            delta = timedelta(days=182)
        portfolio.next_optimize_at = now + delta

        session.commit()
        return {"success": True, "weights": weights}
    except Exception as e:
        session.rollback()
        log.exception("process_portfolio error for %s", portfolio_id)
        return {"success": False, "error": str(e)}
