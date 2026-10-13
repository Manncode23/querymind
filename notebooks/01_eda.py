"""Stage 2 - Exploratory data analysis of the Kaggle credit card fraud data.

Run from the project root:
    python notebooks/01_eda.py

Outputs:
    docs/figures/*.png    charts
    docs/eda_summary.md   key numbers, reused later in the README
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")  # save charts to files instead of opening windows
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.common.config import PROJECT_ROOT, RAW_CSV
from src.common.logging_setup import get_logger

log = get_logger("eda")

FIG_DIR = PROJECT_ROOT / "docs" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_PATH = PROJECT_ROOT / "docs" / "eda_summary.md"

summary_lines = []


def note(line: str = "") -> None:
    """Print a line and keep it for the summary file."""
    print(line)
    summary_lines.append(line)


def save_fig(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIG_DIR / name, dpi=130)
    plt.close(fig)
    log.info("saved figure %s", name)


# ---------------------------------------------------------------- load
log.info("loading %s", RAW_CSV)
df = pd.read_csv(RAW_CSV)
v_cols = [f"V{i}" for i in range(1, 29)]

# ------------------------------------------------- 1. dataset overview
note("# EDA summary")
note()
note("## 1. Dataset overview")
note(f"- Rows: {len(df):,}   Columns: {df.shape[1]}")
note(f"- Missing values (total): {int(df.isna().sum().sum())}")
dup_count = int(df.duplicated().sum())
note(f"- Exact duplicate rows: {dup_count:,} ({dup_count / len(df):.3%})")
note(f"- Memory usage: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
note()

# --------------------------------------------------- 2. class imbalance
fraud_n = int((df["Class"] == 1).sum())
legit_n = int((df["Class"] == 0).sum())
fraud_rate = fraud_n / len(df)

note("## 2. Class imbalance")
note(f"- Legitimate: {legit_n:,}   Fraud: {fraud_n:,}   Fraud rate: {fraud_rate:.4%}")
note(
    f"- A model that always predicts 'legitimate' is {1 - fraud_rate:.2%} accurate "
    "and catches zero fraud, so accuracy is useless here."
)
note("- Decision: evaluate with PR-AUC, precision and recall.")
note()

fig, ax = plt.subplots(figsize=(5, 4))
ax.bar(["Legitimate", "Fraud"], [legit_n, fraud_n], color=["#4c78a8", "#e45756"])
ax.set_yscale("log")
ax.set_ylabel("Transactions (log scale)")
ax.set_title("Class balance")
for x, val in enumerate([legit_n, fraud_n]):
    ax.text(x, val, f"{val:,}", ha="center", va="bottom")
save_fig(fig, "class_balance.png")

# ------------------------------------------------------ 3. amount
note("## 3. Transaction amount")
for cls, label in [(0, "Legitimate"), (1, "Fraud")]:
    s = df.loc[df["Class"] == cls, "Amount"]
    note(
        f"- {label}: mean={s.mean():.2f}  median={s.median():.2f}  "
        f"max={s.max():.2f}"
    )
zero_amount = int((df["Amount"] == 0).sum())
note(f"- Transactions with Amount == 0: {zero_amount:,}")
note(
    f"- Amount: mean={df['Amount'].mean():.2f}, std={df['Amount'].std():.2f} "
    "(heavily right-skewed; V features are already centred, Amount is not)."
)
note("- Decision: scale Amount (and Time) before linear models; consider log1p(Amount).")
note()

fig, ax = plt.subplots(figsize=(7, 4))
for cls, label, color in [(0, "Legitimate", "#4c78a8"), (1, "Fraud", "#e45756")]:
    ax.hist(
        np.log1p(df.loc[df["Class"] == cls, "Amount"]),
        bins=50,
        alpha=0.6,
        density=True,
        label=label,
        color=color,
    )
ax.set_xlabel("log(1 + Amount)")
ax.set_ylabel("Density")
ax.set_title("Amount distribution by class")
ax.legend()
save_fig(fig, "amount_by_class.png")

# -------------------------------------------------------- 4. time
note("## 4. Time")
span_hours = df["Time"].max() / 3600
note(f"- Time is seconds since the first transaction; the data spans {span_hours:.1f} hours.")
df["hour"] = ((df["Time"] // 3600) % 24).astype(int)
hourly = df.groupby("hour")["Class"].agg(["count", "sum"])
hourly["rate"] = hourly["sum"] / hourly["count"]
peak_hour = int(hourly["rate"].idxmax())
note(
    f"- Highest fraud rate is at relative hour {peak_hour} "
    f"({hourly['rate'].max():.3%} vs overall {fraud_rate:.3%}). "
    "Hours are relative to the start of the data, not clock time."
)
note()

fig, ax = plt.subplots(figsize=(8, 4))
ax.bar(hourly.index, hourly["rate"] * 100, color="#e45756")
ax.set_xlabel("Relative hour of day")
ax.set_ylabel("Fraud rate (%)")
ax.set_title("Fraud rate by relative hour")
save_fig(fig, "fraud_rate_by_hour.png")

# ------------------------------------------- 5. feature separation
fraud_df = df[df["Class"] == 1]
legit_df = df[df["Class"] == 0]
pooled_std = np.sqrt((fraud_df[v_cols].var() + legit_df[v_cols].var()) / 2)
effect = (fraud_df[v_cols].mean() - legit_df[v_cols].mean()) / pooled_std
top_features = effect.abs().sort_values(ascending=False).head(10).index.tolist()

note("## 5. Which features separate fraud from legitimate?")
note("- Standardised mean difference (fraud mean - legit mean, in pooled std units):")
for feat in top_features:
    note(f"  - {feat}: {effect[feat]:+.2f}")

corr = df[v_cols].corr().abs().values
np.fill_diagonal(corr, 0)
note(f"- Largest correlation between any two V features: {corr.max():.3f}")
note("- V1-V28 are PCA components, so they are almost uncorrelated with each other.")
note("- Decision: the real fraud signal is in the V features and Amount.")
note()

fig, ax = plt.subplots(figsize=(7, 4))
ax.barh(top_features[::-1], effect[top_features[::-1]], color="#4c78a8")
ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Standardised mean difference (fraud - legitimate)")
ax.set_title("Top 10 separating features")
save_fig(fig, "top_feature_effect.png")

fig, axes = plt.subplots(2, 2, figsize=(9, 6))
for ax, feat in zip(axes.ravel(), top_features[:4]):
    lo, hi = df[feat].quantile([0.01, 0.99])
    ax.hist(legit_df[feat].clip(lo, hi), bins=50, alpha=0.6, density=True,
            label="Legitimate", color="#4c78a8")
    ax.hist(fraud_df[feat].clip(lo, hi), bins=50, alpha=0.6, density=True,
            label="Fraud", color="#e45756")
    ax.set_title(feat)
axes[0, 0].legend()
fig.suptitle("Distributions of the four most separating features")
save_fig(fig, "top_features_distribution.png")

# ------------------------------------------- 6. time-based split check
cutoff = df["Time"].quantile(0.8)
train = df[df["Time"] <= cutoff]
test = df[df["Time"] > cutoff]
train_fraud = int(train["Class"].sum())
test_fraud = int(test["Class"].sum())

note("## 6. Time-based split check (first 80% of time = train, last 20% = test)")
note(f"- Train: {len(train):,} rows, {train_fraud} fraud ({train['Class'].mean():.4%})")
note(f"- Test:  {len(test):,} rows, {test_fraud} fraud ({test['Class'].mean():.4%})")
if test_fraud < 50:
    note("- WARNING: very few fraud cases in the test period; metrics will be noisy.")
else:
    note("- The test period has enough fraud cases for a meaningful evaluation.")
note("- Decision: split by time, not randomly, to avoid leaking future information.")
note()

# ------------------------------------------- 7. design implications
note("## 7. Design implications")
note("- Metrics: PR-AUC, precision, recall; the threshold is chosen from a cost trade-off.")
note("- Split: time-based at the 80th percentile of Time.")
note("- Preprocessing: scale Amount and Time; V features are already centred.")
note("- Schema: customers, accounts and merchants are synthetic context only.")
note("- Duplicates: the dataset has no transaction ID, so the pipeline assigns one;")
note("  the policy for exact duplicate rows is decided in the schema stage.")

SUMMARY_PATH.write_text("\n".join(summary_lines), encoding="utf-8")
log.info("wrote %s", SUMMARY_PATH)