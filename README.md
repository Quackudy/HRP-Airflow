# HRP Portfolio Platform

A complete production-grade portfolio optimization platform based on Hierarchical Risk Parity (HRP) model.

## Architecture

- **Backend**: FastAPI with JWT authentication
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Scheduler**: Apache Airflow for data pipelines and optimization
- **Frontend**: React with modern UI
- **Core Logic**: riskfolio-lib, quantstats, pandas, yfinance

## Quick Start

### 1. Database Setup
```bash
# Create PostgreSQL database
createdb hrp

# Apply schema (optional - tables auto-created on startup)
psql hrp < db/schema.sql
```

### 2. Install Dependencies
```bash
# Install Python dependencies
uv pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install
```

### 3. Environment Variables
```bash
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/hrp"
export JWT_SECRET="your-secret-key-change-in-production"
export JWT_ALGORITHM="HS256"
```

### 4. Run the Platform
```bash
# Start both backend and frontend
./start.sh
```

Or run individually:
```bash
# Backend API
source .venv/bin/activate
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend (in another terminal)
cd frontend
VITE_API_URL=http://localhost:8000 npm run dev
```

## API Endpoints

- **Authentication**: `/auth/register`, `/auth/login`
- **Portfolios**: `/portfolios` (CRUD operations)
- **Reports**: `/portfolios/{id}/report`, `/portfolios/{id}/report/html`
- **API Docs**: http://localhost:8000/docs

## Airflow DAGs

- `update_daily_prices`: Daily price updates (01:00 UTC)
- `portfolio_optimization_sensor`: Triggers optimization (02:00 UTC)
- `run_hrp_optimization`: HRP optimization execution

## Frontend

- **Login/Register**: User authentication
- **Dashboard**: Portfolio management
- **Portfolio Detail**: View weights and reports

## Database Schema

- `users`: User accounts with JWT authentication
- `portfolios`: Portfolio configurations
- `portfolio_weights`: Optimization results
- `daily_prices`: Historical price data


