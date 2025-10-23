import os
import json
import pandas as pd
import pendulum
from datetime import timezone, timedelta
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
    return mapping.get(interval, timedelta(days=30))


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
            
            return {
                "id": row["id"],
                "tickers": row["stock_tickers"],
                "objective": row["objective_function"],
                "interval": row["rebalance_interval"]
            }

    @task()
    def get_price_data(tickers: list):
        """Get historical price data for portfolio tickers."""
        with engine.connect() as conn:
            # SQLite-compatible query using IN clause instead of ANY
            placeholders = ','.join(['?' for _ in tickers])
            prices = conn.execute(text(f"""
                SELECT ticker, date, COALESCE(adj_close, close) AS close
                FROM daily_prices
                WHERE ticker IN ({placeholders})
                ORDER BY date ASC
                """
            ), tickers).mappings().all()
            
            if not prices:
                raise ValueError("No price data available")
            
            df = pd.DataFrame(prices)
            price_pivot = df.pivot(index="date", columns="ticker", values="close").dropna(how='all')
            returns = price_pivot.pct_change().dropna()
            
            return returns

    @task()
    def run_hrp_optimization(returns: pd.DataFrame, portfolio_config: dict):
        """Run HRP optimization using riskfolio-lib."""
        try:
            import riskfolio as rp  # type: ignore
            
            port = rp.Portfolio(returns=returns)
            port.assets_stats(method_mu='hist', method_cov='ledoit', d=0.94)
            weights = port.hrp_portfolio(leaf_order=True)
            weights_dict = weights.squeeze().to_dict()
            
            return {
                "weights": weights_dict,
                "method": "HRP",
                "success": True
            }
        except Exception as e:
            # Fallback: equal weights
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
            # Save weights with current timestamp
            now_ts = datetime.now(timezone.utc).isoformat()
            conn.execute(text(
                """
                INSERT INTO portfolio_weights (portfolio_id, calculation_date, weights)
                VALUES (:pid, :calc_date, :weights)
                """
            ), {
                "pid": portfolio_id,
                "calc_date": now_ts,
                "weights": json.dumps(optimization_result["weights"])
            })
            
            # Update portfolio schedule with computed timestamps
            delta = _rebalance_delta(portfolio_config["interval"])
            next_ts = (datetime.now(timezone.utc) + delta).isoformat()
            conn.execute(text(
                """
                UPDATE portfolios
                SET last_optimized_at = :now_ts, next_optimize_at = :next_ts
                WHERE id = :pid
                """
            ), {"pid": portfolio_id, "now_ts": now_ts, "next_ts": next_ts})
        
        return {
            "portfolio_id": portfolio_id,
            "weights_count": len(optimization_result["weights"]),
            "method": optimization_result["method"],
            "success": optimization_result["success"]
        }

    # Build the flow - this DAG expects portfolio_id from trigger context
    # Note: In TaskFlow, we need to handle the trigger context differently
    # For now, we'll create a simple task that gets the portfolio_id from context
    
    @task()
    def get_portfolio_id_from_context():
        """Extract portfolio_id from DAG run context."""
        from airflow.sdk import get_current_context
        context = get_current_context()
        conf = context.get('dag_run', {}).get('conf', {})
        portfolio_id = conf.get('portfolio_id')
        
        if not portfolio_id:
            raise ValueError("portfolio_id is required in DAG run configuration")
        
        return portfolio_id

    # Build the flow
    portfolio_id = get_portfolio_id_from_context()
    portfolio_config = get_portfolio_config(portfolio_id)
    returns = get_price_data(portfolio_config["tickers"])
    optimization_result = run_hrp_optimization(returns, portfolio_config)
    final_result = save_weights_and_schedule(portfolio_id, optimization_result, portfolio_config)


# Instantiate the DAG
run_hrp_optimization()


