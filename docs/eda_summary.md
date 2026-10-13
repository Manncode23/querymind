# EDA summary

## 1. Dataset overview
- Rows: 284,807   Columns: 31
- Missing values (total): 0
- Exact duplicate rows: 1,081 (0.380%)
- Memory usage: 70.6 MB

## 2. Class imbalance
- Legitimate: 284,315   Fraud: 492   Fraud rate: 0.1727%
- A model that always predicts 'legitimate' is 99.83% accurate and catches zero fraud, so accuracy is useless here.
- Decision: evaluate with PR-AUC, precision and recall.

## 3. Transaction amount
- Legitimate: mean=88.29  median=22.00  max=25691.16
- Fraud: mean=122.21  median=9.25  max=2125.87
- Transactions with Amount == 0: 1,825
- Amount: mean=88.35, std=250.12 (heavily right-skewed; V features are already centred, Amount is not).
- Decision: scale Amount (and Time) before linear models; consider log1p(Amount).

## 4. Time
- Time is seconds since the first transaction; the data spans 48.0 hours.
- Highest fraud rate is at relative hour 2 (1.713% vs overall 0.173%). Hours are relative to the start of the data, not clock time.

## 5. Which features separate fraud from legitimate?
- Standardised mean difference (fraud mean - legit mean, in pooled std units):
  - V14: -2.26
  - V4: +2.01
  - V11: +1.88
  - V12: -1.87
  - V10: -1.61
  - V16: -1.48
  - V3: -1.37
  - V17: -1.35
  - V9: -1.34
  - V2: +1.12
- Largest correlation between any two V features: 0.000
- V1-V28 are PCA components, so they are almost uncorrelated with each other.
- Decision: the real fraud signal is in the V features and Amount.

## 6. Time-based split check (first 80% of time = train, last 20% = test)
- Train: 227,845 rows, 417 fraud (0.1830%)
- Test:  56,962 rows, 75 fraud (0.1317%)
- The test period has enough fraud cases for a meaningful evaluation.
- Decision: split by time, not randomly, to avoid leaking future information.

## 7. Design implications
- Metrics: PR-AUC, precision, recall; the threshold is chosen from a cost trade-off.
- Split: time-based at the 80th percentile of Time.
- Preprocessing: scale Amount and Time; V features are already centred.
- Schema: customers, accounts and merchants are synthetic context only.
- Duplicates: the dataset has no transaction ID, so the pipeline assigns one;
  the policy for exact duplicate rows is decided in the schema stage.