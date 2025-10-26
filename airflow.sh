# 1) Point Airflow to this repo’s folders
export AIRFLOW_HOME=$(pwd)/.airflow
export AIRFLOW__CORE__DAGS_FOLDER=$(pwd)/airflow/dags
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# 2) Airflow metadata DB (SQLite is fine for dev)
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=sqlite:///${AIRFLOW_HOME}/airflow.db

# 3) App DB used by DAGs (same one your FastAPI uses; SQLite works for dev)
export DATABASE_URL=sqlite:///${PWD}/hrp.db

# 4) Webserver port (defaults to 8080; change if needed)
export AIRFLOW__WEBSERVER__WEB_SERVER_PORT=8080

# 5) Start Airflow standalone via uv (uses your .venv)
source .venv/bin/activate
uv run airflow standalone
