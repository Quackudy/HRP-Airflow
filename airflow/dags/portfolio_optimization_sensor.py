import os
import pendulum
from airflow.sdk import dag, task
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from sqlalchemy import create_engine, text


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/hrp")
engine = create_engine(DATABASE_URL)


@dag(
    dag_id="portfolio_optimization_sensor",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="0 2 * * *",
    catchup=False,
    tags=["hrp", "optimization"],
)
def portfolio_optimization_sensor():
    """
    Sensor DAG that checks for portfolios due for optimization and triggers HRP optimization runs.
    """
    
    @task()
    def find_due_portfolios() -> list[dict]:
        """Return list of conf dicts for portfolios due for optimization."""
        with engine.connect() as conn:
            result = conn.execute(text(
                """
                SELECT id FROM portfolios WHERE next_optimize_at <= CURRENT_TIMESTAMP
                """
            ))
            ids = [row[0] for row in result]
        return [{"portfolio_id": pid} for pid in ids]

    confs = find_due_portfolios()
    TriggerDagRunOperator.partial(
        task_id="trigger_hrp_runs",
        trigger_dag_id="run_hrp_optimization",
        reset_dag_run=True,
        wait_for_completion=False,
    ).expand(conf=confs)


portfolio_optimization_sensor()


