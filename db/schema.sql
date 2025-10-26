-- PostgreSQL schema for HRP platform

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    hashed_password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    stock_tickers JSONB NOT NULL,
    objective_function TEXT NOT NULL,
    rebalance_interval TEXT NOT NULL,
    period TEXT NOT NULL,
    last_optimized_at TIMESTAMP WITH TIME ZONE,
    next_optimize_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS portfolio_weights (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER NOT NULL REFERENCES portfolios(id) ON DELETE CASCADE,
    calculation_date TIMESTAMP WITH TIME ZONE NOT NULL,
    weights JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_prices (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    date DATE NOT NULL,
    open DOUBLE PRECISION,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    close DOUBLE PRECISION,
    adj_close DOUBLE PRECISION,
    volume BIGINT
);

-- Unique index for (ticker, date)
CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_prices_ticker_date ON daily_prices (ticker, date);


