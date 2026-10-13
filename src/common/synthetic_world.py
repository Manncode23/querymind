"""Definition of the synthetic world around the real Kaggle transactions.

The Kaggle data has no customers, accounts or merchants. We generate them and
link every transaction with a fixed formula of its transaction_id. The links
are random with respect to fraud: customers and merchants carry NO fraud
signal. All real signal lives in the V1-V28 features and Amount.

The assignment functions are pure and work on single ints or numpy arrays, so
the Kafka producer (one record at a time) and Spark (whole columns) produce
identical results.
"""
from datetime import datetime

import numpy as np

# The dataset only has relative seconds. Anchor assumed from the dataset
# description (September 2013).
DATA_START = datetime(2013, 9, 1)

N_CUSTOMERS = 2_000
N_ACCOUNTS = 3_000
N_MERCHANTS = 300

ACCOUNT_TYPES = ["checking", "savings", "credit"]
MERCHANT_CATEGORIES = [
    "grocery", "electronics", "travel", "dining", "fuel",
    "online_retail", "entertainment", "utilities", "health", "clothing",
]

_MULTIPLIER = 2_654_435_761  # Knuth multiplicative hash constant
_MODULUS = 4_294_967_296     # 2**32
_ACCOUNT_SALT = 1_000_003
_MERCHANT_SALT = 7_000_029


def _mix(transaction_id, salt: int):
    ids = np.asarray(transaction_id, dtype=np.int64)
    return ((ids + salt) * _MULTIPLIER) % _MODULUS


def assign_account_id(transaction_id):
    """Account (1..N_ACCOUNTS) a transaction belongs to."""
    return _mix(transaction_id, _ACCOUNT_SALT) % N_ACCOUNTS + 1


def assign_merchant_id(transaction_id):
    """Merchant (1..N_MERCHANTS) a transaction happened at."""
    return _mix(transaction_id, _MERCHANT_SALT) % N_MERCHANTS + 1


def customer_for_account(account_id):
    """Owner of an account. Every customer ends up with 1 or 2 accounts."""
    ids = np.asarray(account_id, dtype=np.int64)
    return (ids - 1) % N_CUSTOMERS + 1