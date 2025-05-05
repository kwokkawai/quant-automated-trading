-- Create the sequence
CREATE SEQUENCE portfolio_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

-- Create the table
CREATE TABLE IF NOT EXISTS public.portfolio
(
    id integer NOT NULL DEFAULT nextval('portfolio_id_seq'::regclass),
    symbol character varying(10) COLLATE pg_catalog."default",
    quantity integer,
    purchase_price numeric,
    current_price numeric,
    pvalue numeric,
    gain_loss numeric,
    last_updated timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    create_date timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT portfolio_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.stock_orders
(
    id integer NOT NULL DEFAULT nextval('stock_orders_id_seq'::regclass),
    symbol character varying(10) COLLATE pg_catalog."default" NOT NULL,
    order_type character varying(4) COLLATE pg_catalog."default" NOT NULL,
    target_price numeric NOT NULL,
    quantity integer NOT NULL,
    status character varying(10) COLLATE pg_catalog."default" DEFAULT 'PENDING'::character varying,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT stock_orders_pkey PRIMARY KEY (id)
)

CREATE TABLE IF NOT EXISTS public.backtest_results (
    batch_id NUMERIC,
    id SERIAL,
    ticker_code VARCHAR(16) NOT NULL,
    strategy_class VARCHAR(64) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    sharpe_ratio NUMERIC,
    sortino_ratio NUMERIC,
    total_return NUMERIC,
    buy_hold_return NUMERIC,
    annual_return NUMERIC,
    annual_volatility NUMERIC,
    calmar_ratio NUMERIC,
    max_drawdown NUMERIC,
    avg_drawdown NUMERIC,
    max_drawdown_duration INTERVAL,
    avg_drawdown_duration INTERVAL,
    trades INTEGER,
    win_rate NUMERIC,
    best_trade NUMERIC,
    worst_trade NUMERIC,
    avg_trade NUMERIC,
    max_trade_duration INTERVAL,
    avg_trade_duration INTERVAL,
    profit_factor NUMERIC,
    expectancy NUMERIC,
    sqn NUMERIC,
    equity_final NUMERIC,
    equity_peak NUMERIC,
    exposure_time NUMERIC,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (batch_id, id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.portfolio
    OWNER to postgres;