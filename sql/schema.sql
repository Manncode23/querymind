-- QueryMind serving-layer schema (PostgreSQL).
-- Re-running this file drops and recreates every table.

DROP TABLE IF EXISTS fraud_scores CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS accounts CASCADE;
DROP TABLE IF EXISTS merchants CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

CREATE TABLE customers (
    customer_id  INTEGER      PRIMARY KEY,
    full_name    VARCHAR(120) NOT NULL,
    country      VARCHAR(80)  NOT NULL,
    signup_date  DATE         NOT NULL
);

CREATE TABLE merchants (
    merchant_id    INTEGER      PRIMARY KEY,
    merchant_name  VARCHAR(150) NOT NULL,
    category       VARCHAR(40)  NOT NULL
);

CREATE TABLE accounts (
    account_id    INTEGER     PRIMARY KEY,
    customer_id   INTEGER     NOT NULL REFERENCES customers (customer_id),
    account_type  VARCHAR(20) NOT NULL
                  CHECK (account_type IN ('checking', 'savings', 'credit')),
    opened_date   DATE        NOT NULL
);

CREATE TABLE transactions (
    transaction_id  BIGINT         PRIMARY KEY,
    account_id      INTEGER        NOT NULL REFERENCES accounts (account_id),
    merchant_id     INTEGER        NOT NULL REFERENCES merchants (merchant_id),
    txn_time        TIMESTAMP      NOT NULL,
    amount          NUMERIC(12, 2) NOT NULL CHECK (amount >= 0),
    is_fraud        BOOLEAN        NOT NULL
);

CREATE TABLE fraud_scores (
    transaction_id     BIGINT        PRIMARY KEY REFERENCES transactions (transaction_id),
    model_version      VARCHAR(40)   NOT NULL,
    fraud_probability  NUMERIC(7, 6) NOT NULL
                       CHECK (fraud_probability BETWEEN 0 AND 1),
    predicted_fraud    BOOLEAN       NOT NULL,
    scored_at          TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_accounts_customer ON accounts (customer_id);
CREATE INDEX idx_txn_account       ON transactions (account_id);
CREATE INDEX idx_txn_merchant      ON transactions (merchant_id);
CREATE INDEX idx_txn_time          ON transactions (txn_time);
CREATE INDEX idx_txn_fraud_time    ON transactions (txn_time) WHERE is_fraud;
CREATE INDEX idx_scores_predicted  ON fraud_scores (predicted_fraud);