import os
import pandas as pd
import yfinance as yf
import pendulum
from airflow.sdk import dag, task
from sqlalchemy import create_engine, text


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
    Extracts tickers from portfolios, downloads prices via yfinance, and upserts to database.
    """
    
    @task()
    def get_all_tickers():
        """Extract all unique tickers from portfolios table."""
        with engine.connect() as conn:
            # SQLite-compatible query to extract tickers from JSON array
            result = conn.execute(text("""
                SELECT DISTINCT json_each.value 
                FROM portfolios, json_each(stock_tickers) 
                WHERE json_each.value IS NOT NULL
            """))
            # Get all rows first, then clean
            raw_tickers = [row[0] for row in result]
            # Clean ticker symbols by removing quotes and whitespace
            tickers = [t.strip().strip('"').strip("'") for t in raw_tickers if t]
            # Filter out empty strings and invalid symbols
            tickers = [t for t in tickers if t and not t.startswith('{') and not t.endswith('}')]
        return tickers

    @task()
    def download_prices(tickers: list):
        """Download latest price data for all tickers using yfinance."""
        if not tickers:
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
                    # Convert Timestamps to strings for serialization
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    prices[ticker] = df.to_dict(orient='records')
        else:
            df = data.reset_index().rename(columns={
                'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 
                'Close': 'close', 'Adj Close': 'adj_close', 'Volume': 'volume'
            })
            # Convert Timestamps to strings for serialization
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            if len(tickers) == 1:
                prices[tickers[0]] = df.to_dict(orient='records')
        
        return prices

    @task()
    def upsert_prices(prices_data: dict):
        """Upsert price data to daily_prices table."""
        if not prices_data:
            return "No prices to upsert"
        
        with engine.begin() as conn:
            for ticker, rows in prices_data.items():
                for r in rows:
                    # SQLite-compatible upsert using INSERT OR REPLACE
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
        
        return f"Upserted prices for {len(prices_data)} tickers"

    # Build the flow
    tickers = get_all_tickers()
    prices_data = download_prices(tickers)
    result = upsert_prices(prices_data)


# Instantiate the DAG
update_daily_prices()


