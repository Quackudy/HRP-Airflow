import os
import pandas as pd
import yfinance as yf
import pendulum
import logging
from airflow.sdk import dag, task
from sqlalchemy import create_engine, text

log = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/hrp")
engine = create_engine(DATABASE_URL)


@dag(
    dag_id="update_daily_prices",
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule="0 1 * * *",
    catchup=False,
    tags=["hrp", "data"],
)
def update_daily_prices():
    """
    Daily price update pipeline using TaskFlow API.
    Extracts tickers, downloads prices via yfinance, and upserts to database.
    
    NOTE: This version is reverted to use SQLite-compatible syntax (json_each, INSERT OR REPLACE)
    to match the environment detected from the error log.
    """
    
    @task()
    def get_all_tickers():
        """Extract all unique tickers from portfolios table."""
        with engine.connect() as conn:
    
            result = conn.execute(text("""
                SELECT DISTINCT json_each.value 
                FROM portfolios, json_each(stock_tickers) 
                WHERE json_each.value IS NOT NULL
            """))

            raw_tickers = [row[0] for row in result]
            tickers = [t.strip().strip('"').strip("'") for t in raw_tickers if t]
            tickers = [t for t in tickers if t and not t.startswith('{') and not t.endswith('}')]
            log.info(f"Found {len(tickers)} unique tickers.")
            return tickers

    @task()
    def download_prices(tickers: list):
        """Download latest price data for all tickers using yfinance."""
        if not tickers:
            log.info("No tickers provided to download_prices.")
            return {}
        
        data = yf.download(tickers=tickers, period="5d", interval="1d", group_by='ticker', auto_adjust=False, threads=True)
        prices = {}
        
        if isinstance(data.columns, pd.MultiIndex):
            for ticker in tickers:
                if ticker in data.columns.levels[0]:
                    df = data[ticker].reset_index().rename(columns={
                        'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 
                        'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
                    })
            
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    prices[ticker] = df.to_dict(orient='records')
        elif not data.empty and len(tickers) == 1:
            # Handle single-ticker case
            df = data.reset_index().rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
            })

            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            prices[tickers[0]] = df.to_dict(orient='records')
        
        log.info(f"Downloaded price data for {len(prices)} tickers.")
        return prices

    @task()
    def upsert_prices(prices_data: dict):
        """Upsert price data to daily_prices table."""
        if not prices_data:
            log.info("No prices to upsert.")
            return "No prices to upsert"
        
        upsert_count = 0
        with engine.begin() as conn:
            for ticker, rows in prices_data.items():
                if not isinstance(rows, list):
                    log.warning(f"Skipping {ticker}, invalid data format: {rows}")
                    continue
                
                for r in rows:
                    if not isinstance(r, dict):
                        log.warning(f"Skipping row for {ticker}, invalid row format: {r}")
                        continue
                        
                    conn.execute(text(
                        """
                        INSERT OR REPLACE INTO daily_prices (ticker, date, open, high, low, close, adj_close, volume)
                        VALUES (:ticker, :date, :open, :high, :low, :close, :adj_close, :volume)
                        """
                    ), {
                        'ticker': ticker,
                        'date': pd.to_datetime(r['date']).date(),
                        'open': None if pd.isna(r.get('open')) else float(r.get('open')),
                        'high': None if pd.isna(r.get('high')) else float(r.get('high')),
                        'low': None if pd.isna(r.get('low')) else float(r.get('low')),
                        'close': None if pd.isna(r.get('close')) else float(r.get('close')),
                        'adj_close': None if pd.isna(r.get('adj_close')) else float(r.get('adj_close')),
                        'volume': None if pd.isna(r.get('volume')) else int(r.get('volume')),
                    })
                    upsert_count += 1
        
        log.info(f"Upserted {upsert_count} price records for {len(prices_data)} tickers.")
        return f"Upserted prices for {len(prices_data)} tickers"

    tickers = get_all_tickers()
    prices_data = download_prices(tickers)
    result = upsert_prices(prices_data)


update_daily_prices()
