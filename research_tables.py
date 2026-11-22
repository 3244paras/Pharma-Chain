# ==========================================================
# PHARMACEUTICAL BLOCKCHAIN
# RESEARCH TABLE GENERATOR
# ==========================================================

import pandas as pd


# ==========================================================
# DATASET SELECTION
# ==========================================================

print("\n" + "=" * 70)
print("             PHARMACEUTICAL RESEARCH TABLES")
print("=" * 70)

print("\nSelect the dataset:")
print("1. Simulation Data")
print("2. Manual Data")

choice = input("\nEnter your choice (1/2): ").strip()


if choice == "1":
    INPUT_FILE = "experiment_results.csv"
    OUTPUT_FILE = "research_tables.csv"

elif choice == "2":
    INPUT_FILE = "manual_results.csv"
    OUTPUT_FILE = "manual_research_tables.csv"

else:
    print("\nInvalid choice.")
    exit()


# ==========================================================
# LOAD DATA
# ==========================================================

try:
    df = pd.read_csv(INPUT_FILE)

except FileNotFoundError:
    print(f"\nERROR: {INPUT_FILE} was not found.")
    exit()


print(f"\nLoaded {len(df)} records.")
print(f"Dataset: {INPUT_FILE}")


# ==========================================================
# CLEAN COLUMN NAMES
# ==========================================================

df.columns = (
    df.columns
    .astype(str)
    .str.replace("*", "", regex=False)
    .str.strip()
)


# ==========================================================
# FIND COLUMN
# ==========================================================

def find_column(names):

    for name in names:

        if name in df.columns:
            return name

        for column in df.columns:

            if column.lower().strip() == name.lower().strip():
                return column

    return None


atc_col = find_column([
    "ATC",
    "ATC Score",
    "atc_score"
])

macs_col = find_column([
    "MACS",
    "MACS Score",
    "macs_score"
])

pti_col = find_column([
    "PTI",
    "PTI Score",
    "pti_score"
])

recovery_col = find_column([
    "Recovery",
    "Recovery Score",
    "recovery",
    "recovery_score"
])

counterfeit_col = find_column([
    "Counterfeit",
    "counterfeit"
])

risk_col = find_column([
    "Risk",
    "Risk Level",
    "risk_level"
])

recovery_status_col = find_column([
    "Recovery Status",
    "recovery_status"
])


# ==========================================================
# CONVERT SCORES
# ==========================================================

for column in [
    atc_col,
    macs_col,
    pti_col,
    recovery_col
]:

    if column is not None:

        df[column] = (
            df[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ==========================================================
# TABLE 1 — SCORE STATISTICS
# ==========================================================

rows = []

for name, column in [
    ("ATC", atc_col),
    ("MACS", macs_col),
    ("PTI", pti_col),
    ("Recovery Score", recovery_col)
]:

    if column is not None:

        rows.append({
            "Metric": name,
            "Average": round(df[column].mean(), 2),
            "Minimum": round(df[column].min(), 2),
            "Maximum": round(df[column].max(), 2)
        })


score_table = pd.DataFrame(rows)


print("\n")
print("=" * 70)
print("              TABLE 1 — SCORE STATISTICS")
print("=" * 70)

print(score_table.to_string(index=False))


# ==========================================================
# TABLE 2 — COUNTERFEIT CLASSIFICATION
# ==========================================================

if counterfeit_col:

    counterfeit = (
        df[counterfeit_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    counts = counterfeit.value_counts()

    total = len(df)

    counterfeit_rows = []

    for category in ["NO", "POSSIBLE", "YES"]:

        count = counts.get(category, 0)

        counterfeit_rows.append({
            "Authenticity Classification": category,
            "Number of Medicines": count,
            "Percentage": round(
                count / total * 100,
                2
            )
        })

    counterfeit_table = pd.DataFrame(
        counterfeit_rows
    )

else:

    counterfeit_table = pd.DataFrame()


print("\n")
print("=" * 70)
print("        TABLE 2 — AUTHENTICITY CLASSIFICATION")
print("=" * 70)

if not counterfeit_table.empty:
    print(
        counterfeit_table.to_string(
            index=False
        )
    )
else:
    print("Counterfeit data not available.")


# ==========================================================
# TABLE 3 — RISK LEVEL
# ==========================================================

if risk_col:

    risk = (
        df[risk_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    counts = risk.value_counts()

    total = len(df)

    risk_rows = []

    for category in ["LOW", "MEDIUM", "HIGH"]:

        count = counts.get(category, 0)

        risk_rows.append({
            "Risk Level": category,
            "Number of Medicines": count,
            "Percentage": round(
                count / total * 100,
                2
            )
        })

    risk_table = pd.DataFrame(
        risk_rows
    )

else:

    risk_table = pd.DataFrame()


print("\n")
print("=" * 70)
print("              TABLE 3 — RISK LEVEL")
print("=" * 70)

if not risk_table.empty:
    print(
        risk_table.to_string(
            index=False
        )
    )
else:
    print("Risk data not available.")


# ==========================================================
# TABLE 4 — RECOVERY STATUS
# ==========================================================

if recovery_status_col:

    recovery_status = (
        df[recovery_status_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    counts = recovery_status.value_counts()

    total = len(df)

    recovery_rows = []

    categories = [
        "HEALTHY",
        "STABLE",
        "RECOVERING",
        "DEGRADED",
        "CRITICAL"
    ]

    for category in categories:

        count = counts.get(
            category,
            0
        )

        recovery_rows.append({
            "Recovery Status": category,
            "Number of Medicines": count,
            "Percentage": round(
                count / total * 100,
                2
            )
        })

    recovery_table = pd.DataFrame(
        recovery_rows
    )

else:

    recovery_table = pd.DataFrame()


print("\n")
print("=" * 70)
print("             TABLE 4 — RECOVERY STATUS")
print("=" * 70)

if not recovery_table.empty:
    print(
        recovery_table.to_string(
            index=False
        )
    )
else:
    print("Recovery status data not available.")


# ==========================================================
# TABLE 5 — FRAMEWORK COMPONENT COMPARISON
# ==========================================================

framework_rows = []

if atc_col:
    framework_rows.append({
        "Framework Component": "ATC",
        "Average Score": round(
            df[atc_col].mean(),
            2
        )
    })

if macs_col:
    framework_rows.append({
        "Framework Component": "MACS",
        "Average Score": round(
            df[macs_col].mean(),
            2
        )
    })

if pti_col:
    framework_rows.append({
        "Framework Component": "PTI",
        "Average Score": round(
            df[pti_col].mean(),
            2
        )
    })

if recovery_col:
    framework_rows.append({
        "Framework Component":
            "Self-Healing Recovery",
        "Average Score": round(
            df[recovery_col].mean(),
            2
        )
    })


if framework_rows:

    component_average = sum(
        row["Average Score"]
        for row in framework_rows
    ) / len(framework_rows)

    framework_rows.append({
        "Framework Component":
            "Overall Framework",
        "Average Score":
            round(component_average, 2)
    })


framework_table = pd.DataFrame(
    framework_rows
)


print("\n")
print("=" * 70)
print("       TABLE 5 — FRAMEWORK COMPONENT COMPARISON")
print("=" * 70)

print(
    framework_table.to_string(
        index=False
    )
)


# ==========================================================
# SAVE ALL TABLES
# ==========================================================

# Add table identifier before combining

score_table["Table"] = "Score Statistics"

if not counterfeit_table.empty:
    counterfeit_save = counterfeit_table.copy()
    counterfeit_save["Table"] = (
        "Authenticity Classification"
    )
else:
    counterfeit_save = pd.DataFrame()

if not risk_table.empty:
    risk_save = risk_table.copy()
    risk_save["Table"] = "Risk Level"
else:
    risk_save = pd.DataFrame()

if not recovery_table.empty:
    recovery_save = recovery_table.copy()
    recovery_save["Table"] = "Recovery Status"
else:
    recovery_save = pd.DataFrame()

framework_save = framework_table.copy()
framework_save["Table"] = (
    "Framework Components"
)


# ==========================================================
# SAVE SEPARATE RESEARCH TABLE FILES
# ==========================================================

score_table.to_csv(
    "table_score_statistics.csv",
    index=False
)

if not counterfeit_save.empty:
    counterfeit_save.to_csv(
        "table_authenticity.csv",
        index=False
    )

if not risk_save.empty:
    risk_save.to_csv(
        "table_risk.csv",
        index=False
    )

if not recovery_save.empty:
    recovery_save.to_csv(
        "table_recovery.csv",
        index=False
    )

framework_save.to_csv(
    "table_framework_components.csv",
    index=False
)


# ==========================================================
# SAVE COMBINED TABLE
# ==========================================================

all_tables = pd.concat(
    [
        score_table,
        counterfeit_save,
        risk_save,
        recovery_save,
        framework_save
    ],
    ignore_index=True,
    sort=False
)

all_tables.to_csv(
    OUTPUT_FILE,
    index=False
)


# ==========================================================
# COMPLETION
# ==========================================================

print("\n")
print("=" * 70)

print(
    f"Research tables saved to: "
    f"{OUTPUT_FILE}"
)

print("\nGenerated files:")

print("  table_score_statistics.csv")
print("  table_authenticity.csv")
print("  table_risk.csv")
print("  table_recovery.csv")
print("  table_framework_components.csv")
print(f"  {OUTPUT_FILE}")

print("=" * 70)