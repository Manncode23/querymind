# Design decisions

## Transaction IDs
The Kaggle file has no transaction ID. The ID is the 1-based row position in the
file (1 to 284,807). It is stable, so replaying the stream always produces the
same IDs, which makes ingestion idempotent.

## Exact duplicates
The raw file contains 1,081 rows (0.38%) that are identical across all 30 original
columns. Bronze keeps them (raw data stays raw). Silver drops them by full-row match,
keeping the first occurrence, and logs the count.

## Serving layer vs lake
Postgres holds dimensions, transactions and fraud scores. The 28 PCA features (V1-V28)
stay in the Parquet lake: analysts do not query them, and a smaller schema makes
LLM-generated SQL more reliable.

## Synthetic entities
The dataset has no customers, accounts or merchants. They are generated with a fixed
seed, and each transaction is linked to an account and merchant by a pure function of
its transaction_id (see src/common/synthetic_world.py). The links are independent of the
fraud label, so these dimensions carry no fraud signal. They give the SQL layer realistic
joins and context only. The fraud model learns from V1-V28 and Amount.

## Timestamps
The dataset provides seconds since its first transaction. We add them to an assumed
anchor of 2013-09-01 (the dataset description places the data in September 2013). Customer
signup and account opening dates are generated to precede that anchor.

## Risk attributes
Customers and merchants have no stored risk score. Risk metrics will be derived from
observed fraud rates in the Gold layer instead of being invented.