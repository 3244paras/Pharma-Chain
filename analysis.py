# ==========================================================
# PHARMACEUTICAL BLOCKCHAIN ANALYSIS
# ==========================================================

import pandas as pd
import matplotlib.pyplot as plt


# ==========================================================
# SELECT DATASET
# ==========================================================

print("\n" + "=" * 65)
print("       PHARMACEUTICAL BLOCKCHAIN ANALYSIS")
print("=" * 65)

print("\nSelect the dataset you want to analyze:")

print("1. Simulation Data")
print("2. Manual Data")

choice = input("\nEnter your choice (1/2): ").strip()


if choice == "1":

    INPUT_FILE = "experiment_results.csv"
    OUTPUT_FILE = "experimental_summary.csv"

elif choice == "2":

    INPUT_FILE = "manual_results.csv"
    OUTPUT_FILE = "manual_summary.csv"

else:

    print("\nInvalid choice.")
    print("Please enter 1 or 2.")
    exit()


# ==========================================================
# LOAD DATA
# ==========================================================

try:

    df = pd.read_csv(INPUT_FILE)

except FileNotFoundError:

    print(
        f"\nERROR: {INPUT_FILE} was not found."
    )

    print(
        "Make sure the required dataset exists "
        "in the project folder."
    )

    exit()


print(
    f"\nLoaded {len(df)} records."
)

print(
    f"Dataset: {INPUT_FILE}"
)


# ==========================================================
# HELPER FUNCTION
# ==========================================================

def find_column(names):

    for name in names:

        if name in df.columns:
            return name

        for column in df.columns:

            if column.lower() == name.lower():
                return column

    return None


# ==========================================================
# FIND REQUIRED COLUMNS
# ==========================================================

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


# ==========================================================
# CONVERT NUMERIC COLUMNS
# ==========================================================

for column in [
    atc_col,
    macs_col,
    pti_col,
    recovery_col
]:

    if column is not None:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# ==========================================================
# STATISTICAL ANALYSIS
# ==========================================================

print("\n" + "=" * 65)
print("             STATISTICAL ANALYSIS")
print("=" * 65)


if atc_col:

    print(
        f"Average ATC              : "
        f"{df[atc_col].mean():.2f}"
    )

    print(
        f"Minimum ATC              : "
        f"{df[atc_col].min():.2f}"
    )

    print(
        f"Maximum ATC              : "
        f"{df[atc_col].max():.2f}"
    )


if macs_col:

    print(
        f"Average MACS             : "
        f"{df[macs_col].mean():.2f}"
    )

    print(
        f"Minimum MACS             : "
        f"{df[macs_col].min():.2f}"
    )

    print(
        f"Maximum MACS             : "
        f"{df[macs_col].max():.2f}"
    )


if pti_col:

    print(
        f"Average PTI              : "
        f"{df[pti_col].mean():.2f}"
    )

    print(
        f"Minimum PTI              : "
        f"{df[pti_col].min():.2f}"
    )

    print(
        f"Maximum PTI              : "
        f"{df[pti_col].max():.2f}"
    )


if recovery_col:

    print(
        f"Average Recovery         : "
        f"{df[recovery_col].mean():.2f}"
    )

    print(
        f"Minimum Recovery         : "
        f"{df[recovery_col].min():.2f}"
    )

    print(
        f"Maximum Recovery         : "
        f"{df[recovery_col].max():.2f}"
    )


print("=" * 65)


# ==========================================================
# COUNTERFEIT ANALYSIS
# ==========================================================

print("\n" + "=" * 65)
print("             COUNTERFEIT ANALYSIS")
print("=" * 65)


if counterfeit_col:

    counterfeit_counts = (
        df[counterfeit_col]
        .astype(str)
        .str.upper()
        .value_counts()
    )

    total = len(df)

    for category in [
        "NO",
        "POSSIBLE",
        "YES"
    ]:

        count = counterfeit_counts.get(
            category,
            0
        )

        percentage = (
            count / total * 100
        )

        if category == "NO":

            label = "Genuine"

        elif category == "POSSIBLE":

            label = "Possible Counterfeit"

        else:

            label = "Counterfeit"

        print(
            f"{label:<25}: "
            f"{count:>3} "
            f"({percentage:.2f}%)"
        )


print("=" * 65)


# ==========================================================
# RISK ANALYSIS
# ==========================================================

print("\n" + "=" * 65)
print("                 RISK ANALYSIS")
print("=" * 65)


if risk_col:

    risk_counts = (
        df[risk_col]
        .astype(str)
        .str.upper()
        .value_counts()
    )

    total = len(df)

    for category in [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]:

        count = risk_counts.get(
            category,
            0
        )

        percentage = (
            count / total * 100
        )

        print(
            f"{category:<25}: "
            f"{count:>3} "
            f"({percentage:.2f}%)"
        )


print("=" * 65)


# ==========================================================
# CREATE SUMMARY
# ==========================================================

summary = {

    "Dataset": INPUT_FILE,

    "Total Records": len(df),

    "Average ATC":
        round(df[atc_col].mean(), 2)
        if atc_col else None,

    "Minimum ATC":
        round(df[atc_col].min(), 2)
        if atc_col else None,

    "Maximum ATC":
        round(df[atc_col].max(), 2)
        if atc_col else None,

    "Average MACS":
        round(df[macs_col].mean(), 2)
        if macs_col else None,

    "Minimum MACS":
        round(df[macs_col].min(), 2)
        if macs_col else None,

    "Maximum MACS":
        round(df[macs_col].max(), 2)
        if macs_col else None,

    "Average PTI":
        round(df[pti_col].mean(), 2)
        if pti_col else None,

    "Minimum PTI":
        round(df[pti_col].min(), 2)
        if pti_col else None,

    "Maximum PTI":
        round(df[pti_col].max(), 2)
        if pti_col else None,

    "Average Recovery":
        round(df[recovery_col].mean(), 2)
        if recovery_col else None,

    "Minimum Recovery":
        round(df[recovery_col].min(), 2)
        if recovery_col else None,

    "Maximum Recovery":
        round(df[recovery_col].max(), 2)
        if recovery_col else None
}


summary_df = pd.DataFrame(
    [summary]
)


summary_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"\nSummary saved to: {OUTPUT_FILE}"
)


# ==========================================================
# GRAPH GENERATION
# ==========================================================

print("\nGenerating research graphs...")


# ----------------------------------------------------------
# SCORE GRAPH
# ----------------------------------------------------------

if (
    atc_col and
    macs_col and
    pti_col
):

    plt.figure()

    plt.plot(
        df[atc_col],
        label="ATC"
    )

    plt.plot(
        df[macs_col],
        label="MACS"
    )

    plt.plot(
        df[pti_col],
        label="PTI"
    )

    plt.xlabel(
        "Transaction"
    )

    plt.ylabel(
        "Score"
    )

    plt.title(
        "ATC, MACS and PTI Scores"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "graph_scores.png"
    )

    plt.close()


# ----------------------------------------------------------
# COUNTERFEIT GRAPH
# ----------------------------------------------------------

if counterfeit_col:

    counts = (
        df[counterfeit_col]
        .astype(str)
        .str.upper()
        .value_counts()
    )

    categories = [
        "NO",
        "POSSIBLE",
        "YES"
    ]

    values = [
        counts.get(
            category,
            0
        )
        for category in categories
    ]

    plt.figure()

    plt.bar(
        categories,
        values
    )

    plt.xlabel(
        "Counterfeit Classification"
    )

    plt.ylabel(
        "Number of Medicines"
    )

    plt.title(
        "Counterfeit Classification"
    )

    plt.tight_layout()

    plt.savefig(
        "graph_counterfeit.png"
    )

    plt.close()


# ----------------------------------------------------------
# RISK GRAPH
# ----------------------------------------------------------

if risk_col:

    counts = (
        df[risk_col]
        .astype(str)
        .str.upper()
        .value_counts()
    )

    categories = [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]

    values = [
        counts.get(
            category,
            0
        )
        for category in categories
    ]

    plt.figure()

    plt.bar(
        categories,
        values
    )

    plt.xlabel(
        "Risk Level"
    )

    plt.ylabel(
        "Number of Medicines"
    )

    plt.title(
        "Pharmaceutical Risk Distribution"
    )

    plt.tight_layout()

    plt.savefig(
        "graph_risk.png"
    )

    plt.close()


# ----------------------------------------------------------
# RECOVERY GRAPH
# ----------------------------------------------------------

if recovery_col:

    plt.figure()

    plt.plot(
        df[recovery_col],
        label="Recovery Score"
    )

    plt.xlabel(
        "Transaction"
    )

    plt.ylabel(
        "Recovery Score"
    )

    plt.title(
        "Self-Healing Recovery Performance"
    )

    plt.legend()

    plt.tight_layout()

    plt.savefig(
        "graph_recovery.png"
    )

    plt.close()


# ==========================================================
# COMPLETED
# ==========================================================

print("\n" + "=" * 65)
print("             ANALYSIS COMPLETED")
print("=" * 65)

print("\nDataset analyzed:")
print(INPUT_FILE)

print("\nGenerated summary:")
print(OUTPUT_FILE)

print("\nGenerated graphs:")
print("graph_scores.png")
print("graph_counterfeit.png")
print("graph_risk.png")
print("graph_recovery.png")

print("=" * 65)