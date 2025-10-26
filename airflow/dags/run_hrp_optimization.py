import os
import json  # <--- Import JSON module
import pandas as pd
import pendulum
from datetime import datetime, timezone, timedelta  # <--- Import datetime
from airflow.sdk import dag, task
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/hrp")
engine = create_engine(DATABASE_URL)


def _rebalance_delta(interval: str) -> timedelta:
    """Convert rebalance interval string to timedelta."""
    mapping = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30),
        'quarterly': timedelta(days=90),
    }
    return mapping.get(str(interval).lower(), timedelta(days=30))


@dag(
    dag_id="run_hrp_optimization",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule=None,  # Trigger-only DAG
    catchup=False,
    tags=["hrp", "optimization"],
)
def run_hrp_optimization():
    """
    HRP optimization DAG that runs Hierarchical Risk Parity optimization for a specific portfolio.
    Triggered by portfolio_optimization_sensor with portfolio_id parameter.
    """
    
    @task()
    def get_portfolio_config(portfolio_id: int):
        """Get portfolio configuration from database."""
        with engine.connect() as conn:
            row = conn.execute(text("""
                SELECT id, stock_tickers, objective_function, rebalance_interval 
                FROM portfolios WHERE id = :id
            """), {"id": portfolio_id}).mappings().first()
            
            if not row:
                raise ValueError(f"Portfolio {portfolio_id} not found")
            
            try:
                tickers_list = json.loads(row["stock_tickers"])
                if not isinstance(tickers_list, list):
                    tickers_list = []
            except (json.JSONDecodeError, TypeError):
                tickers_list = []
            
            return {
                "id": row["id"],
                "tickers": tickers_list, 
                "objective": row["objective_function"],
                "interval": row["rebalance_interval"]
            }

    @task()
    def get_price_data(tickers: list):
        """Get historical price data for portfolio tickers."""
        if not tickers:
            raise ValueError("No tickers provided from portfolio config")
        
        with engine.connect() as conn:

            placeholders = {f'tic_{i}': ticker for i, ticker in enumerate(tickers)}
            param_names = ', '.join(placeholders.keys())
            
            prices = conn.execute(text(f"""
                SELECT ticker, date, COALESCE(adj_close, close) AS close
                FROM daily_prices
                WHERE ticker IN ({param_names})
                ORDER BY date ASC
            """), placeholders).mappings().all()
            
            if not prices:
                raise ValueError(f"No price data available for tickers: {tickers}")
            
            df = pd.DataFrame(prices)
            price_pivot = df.pivot(index="date", columns="ticker", values="close").fillna(method='ffill')
            
            price_pivot = price_pivot.reindex(columns=tickers).dropna(axis=1, how='all')

            if price_pivot.empty:
                 raise ValueError(f"Price data pivot is empty for tickers: {tickers}")
                 
            returns = price_pivot.pct_change().dropna(how='all')
            
            if returns.empty:
                 raise ValueError(f"Returns calculation resulted in empty dataframe for tickers: {tickers}")

            return returns

    @task()
    def run_hrp_optimization(returns: pd.DataFrame, portfolio_config: dict):
        """Run HRP optimization using riskfolio-lib."""
        try:
            import riskfolio as rp  
            
            port = rp.Portfolio(returns=returns)
            model = portfolio_config.get("objective", "HRP") 
            w = port.optimization(
                model=model,
                rm='MV',
                rf=0, 
                leaf_order=True
            )
            
            weights_dict = w.squeeze().to_dict()
        
            return {
                "weights": weights_dict,
                "method": model,
                "success": True
            }
        except Exception as e:

            n = len(returns.columns)
            weights_dict = {ticker: 1.0 / n for ticker in returns.columns}
            
            return {
                "weights": weights_dict,
                "method": "Equal Weight (fallback)",
                "success": False,
                "error": str(e)
            }

    @task()
    def save_weights_and_schedule(portfolio_id: int, optimization_result: dict, portfolio_config: dict):
        """Save optimization weights and update portfolio schedule."""
        with engine.begin() as conn:

            now = datetime.now(timezone.utc)
            
            conn.execute(text(
                """
                INSERT INTO portfolio_weights (portfolio_id, calculation_date, weights)
                VALUES (:pid, :calc_date, :weights)
                """
            ), {
                "pid": portfolio_id,
                "calc_date": now,
                "weights": json.dumps(optimization_result["weights"])
            })
            
            delta = _rebalance_delta(portfolio_config["interval"])
            next_ts = (now + delta)
            
            conn.execute(text(
                """
                UPDATE portfolios
                SET last_optimized_at = :now_ts, next_optimize_at = :next_ts
                WHERE id = :pid
                """
            ), {"pid": portfolio_id, "now_ts": now, "next_ts": next_ts})
        
        return {
            "portfolio_id": portfolio_id,
            "weights_count": len(optimization_result["weights"]),
            "method": optimization_result["method"],
            "success": optimization_result["success"]
        }

    @task()
    def get_portfolio_id_from_context(dag_run=None):
        """Extract portfolio_id from DAG run context."""
        conf = dag_run.conf if dag_run else {}
        portfolio_id = conf.get('portfolio_id')
        
        if not portfolio_id:
            raise ValueError("portfolio_id is required in DAG run configuration")
        
        return int(portfolio_id)

    portfolio_id = get_portfolio_id_from_context()
    portfolio_config = get_portfolio_config(portfolio_id)
    returns = get_price_data(portfolio_config["tickers"])
    optimization_result = run_hrp_optimization(returns, portfolio_config)
    final_result = save_weights_and_schedule(portfolio_id, optimization_result, portfolio_config)


run_hrp_optimization()
