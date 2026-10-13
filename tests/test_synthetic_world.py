import numpy as np

from src.common import synthetic_world as sw

ALL_IDS = np.arange(1, 284_808)  # every transaction_id in the Kaggle file


def test_assignments_are_in_range():
    accounts = sw.assign_account_id(ALL_IDS)
    merchants = sw.assign_merchant_id(ALL_IDS)
    assert accounts.min() >= 1 and accounts.max() <= sw.N_ACCOUNTS
    assert merchants.min() >= 1 and merchants.max() <= sw.N_MERCHANTS


def test_assignment_is_deterministic():
    first = sw.assign_account_id(ALL_IDS)
    second = sw.assign_account_id(ALL_IDS)
    np.testing.assert_array_equal(first, second)


def test_scalar_matches_vectorised():
    vec_accounts = sw.assign_account_id(ALL_IDS)
    vec_merchants = sw.assign_merchant_id(ALL_IDS)
    for tid in (1, 17, 500, 123_456, 284_807):
        assert int(sw.assign_account_id(tid)) == int(vec_accounts[tid - 1])
        assert int(sw.assign_merchant_id(tid)) == int(vec_merchants[tid - 1])


def test_every_account_and_merchant_gets_transactions():
    accounts = sw.assign_account_id(ALL_IDS)
    merchants = sw.assign_merchant_id(ALL_IDS)
    assert len(np.unique(accounts)) == sw.N_ACCOUNTS
    assert len(np.unique(merchants)) == sw.N_MERCHANTS


def test_load_is_balanced():
    counts = np.bincount(sw.assign_account_id(ALL_IDS), minlength=sw.N_ACCOUNTS + 1)[1:]
    assert counts.max() < 3 * counts.mean()


def test_every_customer_has_an_account():
    owners = sw.customer_for_account(np.arange(1, sw.N_ACCOUNTS + 1))
    assert set(owners.tolist()) == set(range(1, sw.N_CUSTOMERS + 1))