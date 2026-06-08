
# Cricket Match Winner Prediction Model
# ======================================
# ALGORITHM USED: Random Forest Classifier




import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# STEP 1 — LOAD AND PREPARE DATA
# =============================================================================

print("=" * 60)
print("CRICKET MATCH WINNER PREDICTION MODEL")
print("=" * 60)

# ── 1.1  Load the CSV ─────────────────────────────────────────────────────────
# Change the path below if your CSV file has a different name or location.
CSV_PATH = r"Task 2\cricket_data.csv"

print(f"\n[1/4] Loading data from '{CSV_PATH}' ...")
try:
    df = pd.read_csv(CSV_PATH, low_memory=False)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Could not find '{CSV_PATH}'. "
        "Please place your CSV file in the same folder as model.py "
        "and update CSV_PATH if needed."
    )

print(f"      Raw shape: {df.shape[0]:,} rows × {df.shape[1]} columns")

# ── 1.2  Filter to seasons 2020–2026 ─────────────────────────────────────────
df["year"] = pd.to_numeric(df["year"], errors="coerce")
df = df[(df["year"] >= 2020) & (df["year"] <= 2026)].copy()
print(f"      After 2020-2026 filter: {df.shape[0]:,} rows")

# ── 1.3  Drop rows with no match winner (neutral/no-result matches) ───────────
df = df.dropna(subset=["match_won_by"])
df = df[df["match_won_by"].str.strip() != ""]
df = df[~df["match_won_by"].isin(["NA", "N/A", "nan", "NaN"])]

# ── 1.4  Select and clean feature columns ────────────────────────────────────
FEATURE_COLS = [
    "batting_team",
    "bowling_team",
    "venue",
    "toss_winner",
    "toss_decision",
    "innings",
    "over",
    "runs_total",
    "team_runs",
    "team_wicket",
    "team_balls",
]
TARGET_COL = "match_won_by"

# Keep only needed columns
cols_needed = FEATURE_COLS + [TARGET_COL]
# Some columns might be missing in certain versions of the dataset
cols_present = [c for c in cols_needed if c in df.columns]
df = df[cols_present].copy()

# Fill missing numeric values with median
numeric_cols = ["innings", "over", "runs_total", "team_runs", "team_wicket", "team_balls"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df[col] = df[col].fillna(df[col].median())

# Fill missing categorical values with 'Unknown'
cat_cols = ["batting_team", "bowling_team", "venue", "toss_winner", "toss_decision"]
for col in cat_cols:
    if col in df.columns:
        df[col] = df[col].fillna("Unknown").astype(str).str.strip()

df = df.dropna(subset=[TARGET_COL])
df[TARGET_COL] = df[TARGET_COL].astype(str).str.strip()

print(f"      After cleaning: {df.shape[0]:,} rows")
print(f"      Unique match winners: {df[TARGET_COL].nunique()}")

# ── 1.5  Encode categorical features ─────────────────────────────────────────
label_encoders = {}
for col in cat_cols:
    if col in df.columns:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col])
        label_encoders[col] = le

# Encode target
le_target = LabelEncoder()
y = le_target.fit_transform(df[TARGET_COL])
target_classes = le_target.classes_

# Build final feature matrix
feature_names = [c + "_enc" for c in cat_cols if (c + "_enc") in df.columns] + \
                [c for c in numeric_cols if c in df.columns]
X = df[feature_names].values

print(f"\n      Features used ({len(feature_names)}): {feature_names}")

# =============================================================================
# STEP 2 — BUILD THE MODEL
# =============================================================================

print("\n[2/4] Splitting data and training Random Forest ...")

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)
print(f"      Train size: {len(X_train):,}  |  Test size: {len(X_test):,}")

model = RandomForestClassifier(
    n_estimators=200,       # 200 trees — good balance of speed vs accuracy
    max_depth=15,           # prevent overfitting
    min_samples_leaf=5,
    class_weight="balanced",# handles class imbalance (some teams appear more)
    random_state=42,
    n_jobs=-1               # use all CPU cores
)
model.fit(X_train, y_train)
print("      Model trained successfully.")

# =============================================================================
# STEP 3 — EVALUATE THE MODEL
# =============================================================================

print("\n[3/4] Evaluating model on test set ...")

y_pred = model.predict(X_test)

acc   = accuracy_score(y_test, y_pred)
f1    = f1_score(y_test, y_pred, average="weighted", zero_division=0)
cm    = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred,
                                target_names=target_classes,
                                zero_division=0)

print("\n" + "=" * 60)
print("EVALUATION RESULTS")
print("=" * 60)
print(f"  Accuracy Score : {acc:.4f}  ({acc*100:.2f}%)")
print(f"  F1 Score (wtd) : {f1:.4f}")

print("\n  Confusion Matrix:")
print("  (Rows = Actual, Columns = Predicted)")
cm_df = pd.DataFrame(cm, index=target_classes, columns=target_classes)
print(cm_df.to_string())

print("\n  Classification Report:")
print(report)

# =============================================================================
# STEP 4 — FEATURE IMPORTANCE
# =============================================================================

print("[4/4] Feature Importances:")
importances = model.feature_importances_
fi_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": importances
}).sort_values("Importance", ascending=False)

for _, row in fi_df.iterrows():
    bar = "█" * int(row["Importance"] * 80)
    print(f"  {row['Feature']:<22} {row['Importance']:.4f}  {bar}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Algorithm : Random Forest (n_estimators=200, max_depth=15)")
print(f"  Seasons   : 2020 – 2026")
print(f"  Samples   : {len(X):,} balls (train={len(X_train):,}, test={len(X_test):,})")
print(f"  Features  : {len(feature_names)}")
print(f"  Accuracy  : {acc*100:.2f}%")
print(f"  F1 Score  : {f1:.4f}")
print("=" * 60)