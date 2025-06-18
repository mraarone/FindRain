# database/init.sql
-- Initialize TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create tables (if not created by migrations)
CREATE TABLE IF NOT EXISTS market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    open NUMERIC(20, 8),
    high NUMERIC(20, 8),
    low NUMERIC(20, 8),
    close NUMERIC(20, 8),
    volume BIGINT,
    source VARCHAR(50)
);

-- Create hypertable for time-series data
SELECT create_hypertable('market_data', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time 
ON market_data (symbol, time DESC);

-- Set up continuous aggregates for common queries
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    symbol,
    first(open, time) AS open,
    max(high) AS high,
    min(low) AS low,
    last(close, time) AS close,
    sum(volume) AS volume
FROM market_data
GROUP BY bucket, symbol;

-- Refresh policy for continuous aggregate
SELECT add_continuous_aggregate_policy('market_data_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Data retention policy (keep raw data for 1 year)
SELECT add_retention_policy('market_data', INTERVAL '1 year');

-- Compression policy (compress data older than 1 week)
SELECT add_compression_policy('market_data', INTERVAL '1 week');

-- Create additional indexes for performance
CREATE INDEX IF NOT EXISTS idx_news_articles_published 
ON news_articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_api_requests_user_created 
ON api_requests (user_id, created_at DESC);

-- Create functions for common queries
CREATE OR REPLACE FUNCTION get_latest_price(p_symbol VARCHAR)
RETURNS TABLE(symbol VARCHAR, price NUMERIC, timestamp TIMESTAMPTZ)
AS $
BEGIN
    RETURN QUERY
    SELECT 
        md.symbol,
        md.close as price,
        md.time as timestamp
    FROM market_data md
    WHERE md.symbol = p_symbol
    ORDER BY md.time DESC
    LIMIT 1;
END;
$ LANGUAGE plpgsql;

-- Performance optimization settings
ALTER SYSTEM SET shared_buffers = '4GB';
ALTER SYSTEM SET effective_cache_size = '12GB';
ALTER SYSTEM SET maintenance_work_mem = '1GB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '32MB';
ALTER SYSTEM SET min_wal_size = '2GB';
ALTER SYSTEM SET max_wal_size = '4GB';