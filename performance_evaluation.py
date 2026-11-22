# ==========================================================
# PHARMACEUTICAL BLOCKCHAIN
# PERFORMANCE EVALUATION
# ==========================================================

import pandas as pd


# ==========================================================
# SELECT DATASET
# ==========================================================

print("\n" + "=" * 70)
print("          PHARMACEUTICAL PERFORMANCE EVALUATION")
print("=" * 70)

print("\nSelect the dataset you want to evaluate:")
print("1. Simulation Data")
print("2. Manual Data")

choice = input("\nEnter your choice (1/2): ").strip()


if choice == "1":
    INPUT_FILE = "experiment_results.csv"
    OUTPUT_FILE = "performance_results.csv"

elif choice == "2":
    INPUT_FILE = "manual_results.csv"
    OUTPUT_FILE = "manual_performance_results.csv"

else:
    print("\nInvalid choice. Please enter 1 or 2.")
    exit()


# ==========================================================
# LOAD DATA
# ==========================================================

try:

    df = pd.read_csv(INPUT_FILE)

except FileNotFoundError:

    print(f"\nERROR: {INPUT_FILE} was not found.")
    print("Make sure the dataset exists in the project folder.")
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

def find_column(possible_names):

    for name in possible_names:

        if name in df.columns:
            return name

        for column in df.columns:

            if column.lower().strip() == name.lower().strip():
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
    "recovery",
    "recovery_score"
])

atc_status_col = find_column([
    "ATC Status",
    "atc_status"
])

macs_status_col = find_column([
    "MACS Status",
    "macs_status"
])

pti_status_col = find_column([
    "PTI Status",
    "pti_status"
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
# SHOW DETECTED COLUMNS
# ==========================================================

print("\nDetected columns:")

print("ATC      :", atc_col)
print("MACS     :", macs_col)
print("PTI      :", pti_col)
print("Recovery :", recovery_col)


# ==========================================================
# CHECK REQUIRED SCORE COLUMNS
# ==========================================================

if atc_col is None:
    print("\nWARNING: ATC column not found.")

if macs_col is None:
    print("WARNING: MACS column not found.")

if pti_col is None:
    print("WARNING: PTI column not found.")

if recovery_col is None:
    print("WARNING: Recovery column not found.")


# ==========================================================
# CONVERT SCORE COLUMNS TO NUMERIC
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
# DISPLAY DATA QUALITY
# ==========================================================

print("\nData quality check:")

if atc_col:
    print(
        f"ATC valid values      : "
        f"{df[atc_col].notna().sum()}/{len(df)}"
    )

if macs_col:
    print(
        f"MACS valid values     : "
        f"{df[macs_col].notna().sum()}/{len(df)}"
    )

if pti_col:
    print(
        f"PTI valid values      : "
        f"{df[pti_col].notna().sum()}/{len(df)}"
    )

if recovery_col:
    print(
        f"Recovery valid values : "
        f"{df[recovery_col].notna().sum()}/{len(df)}"
    )


# ==========================================================
# AVERAGE SCORES
# ==========================================================

print("\n" + "=" * 70)
print("                 AVERAGE SCORES")
print("=" * 70)


average_atc = (
    df[atc_col].mean()
    if atc_col is not None
    else 0
)

average_macs = (
    df[macs_col].mean()
    if macs_col is not None
    else 0
)

average_pti = (
    df[pti_col].mean()
    if pti_col is not None
    else 0
)

average_recovery = (
    df[recovery_col].mean()
    if recovery_col is not None
    else 0
)


print(
    f"Average ATC             : "
    f"{average_atc:.2f}"
)

print(
    f"Average MACS            : "
    f"{average_macs:.2f}"
)

print(
    f"Average PTI             : "
    f"{average_pti:.2f}"
)

print(
    f"Average Recovery        : "
    f"{average_recovery:.2f}"
)


# ==========================================================
# ATC PERFORMANCE
# ==========================================================

print("\n" + "=" * 70)
print("                 ATC PERFORMANCE")
print("=" * 70)


if atc_status_col:

    status = (
        df[atc_status_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    trusted = (
        status == "TRUSTED"
    ).sum()

    monitor = (
        status == "MONITOR"
    ).sum()

    suspicious = (
        status == "SUSPICIOUS"
    ).sum()

    total = len(df)

    print(
        f"ATC Trusted Transactions : "
        f"{trusted} "
        f"({trusted / total * 100:.2f}%)"
    )

    print(
        f"ATC Monitor Transactions : "
        f"{monitor} "
        f"({monitor / total * 100:.2f}%)"
    )

    print(
        f"ATC Suspicious            : "
        f"{suspicious} "
        f"({suspicious / total * 100:.2f}%)"
    )


# ==========================================================
# MACS PERFORMANCE
# ==========================================================

print("\n" + "=" * 70)
print("                 MACS PERFORMANCE")
print("=" * 70)


if macs_status_col:

    status = (
        df[macs_status_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    genuine = (
        status == "GENUINE"
    ).sum()

    suspicious = (
        status == "SUSPICIOUS"
    ).sum()

    counterfeit_risk = (
        status == "COUNTERFEIT RISK"
    ).sum()

    total = len(df)

    print(
        f"MACS Genuine Transactions : "
        f"{genuine} "
        f"({genuine / total * 100:.2f}%)"
    )

    print(
        f"MACS Suspicious            : "
        f"{suspicious} "
        f"({suspicious / total * 100:.2f}%)"
    )

    print(
        f"MACS Counterfeit Risk      : "
        f"{counterfeit_risk} "
        f"({counterfeit_risk / total * 100:.2f}%)"
    )


# ==========================================================
# PTI PERFORMANCE
# ==========================================================

print("\n" + "=" * 70)
print("                  PTI PERFORMANCE")
print("=" * 70)


if pti_status_col:

    status = (
        df[pti_status_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    highly_trusted = (
        status == "HIGHLY TRUSTED"
    ).sum()

    trusted = (
        status == "TRUSTED"
    ).sum()

    monitor = (
        status == "MONITOR"
    ).sum()

    low_trust = (
        status == "LOW TRUST"
    ).sum()

    total = len(df)

    print(
        f"PTI Highly Trusted       : "
        f"{highly_trusted} "
        f"({highly_trusted / total * 100:.2f}%)"
    )

    print(
        f"PTI Trusted              : "
        f"{trusted} "
        f"({trusted / total * 100:.2f}%)"
    )

    print(
        f"PTI Monitor              : "
        f"{monitor} "
        f"({monitor / total * 100:.2f}%)"
    )

    print(
        f"PTI Low Trust            : "
        f"{low_trust} "
        f"({low_trust / total * 100:.2f}%)"
    )


# ==========================================================
# COUNTERFEIT ANALYSIS
# ==========================================================

print("\n" + "=" * 70)
print("             COUNTERFEIT CLASSIFICATION")
print("=" * 70)


if counterfeit_col:

    status = (
        df[counterfeit_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    no_counterfeit = (
        status == "NO"
    ).sum()

    possible = (
        status == "POSSIBLE"
    ).sum()

    yes_counterfeit = (
        status == "YES"
    ).sum()

    total = len(df)

    print(
        f"NO                       : "
        f"{no_counterfeit:3d} "
        f"({no_counterfeit / total * 100:.2f}%)"
    )

    print(
        f"POSSIBLE                 : "
        f"{possible:3d} "
        f"({possible / total * 100:.2f}%)"
    )

    print(
        f"YES                      : "
        f"{yes_counterfeit:3d} "
        f"({yes_counterfeit / total * 100:.2f}%)"
    )


# ==========================================================
# RISK ANALYSIS
# ==========================================================

print("\n" + "=" * 70)
print("                    RISK ANALYSIS")
print("=" * 70)


if risk_col:

    status = (
        df[risk_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    low = (
        status == "LOW"
    ).sum()

    medium = (
        status == "MEDIUM"
    ).sum()

    high = (
        status == "HIGH"
    ).sum()

    total = len(df)

    print(
        f"LOW                      : "
        f"{low:3d} "
        f"({low / total * 100:.2f}%)"
    )

    print(
        f"MEDIUM                   : "
        f"{medium:3d} "
        f"({medium / total * 100:.2f}%)"
    )

    print(
        f"HIGH                     : "
        f"{high:3d} "
        f"({high / total * 100:.2f}%)"
    )


# ==========================================================
# SELF-HEALING PERFORMANCE
# ==========================================================

print("\n" + "=" * 70)
print("              SELF-HEALING PERFORMANCE")
print("=" * 70)


if recovery_status_col:

    status = (
        df[recovery_status_col]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    healthy = (
        status == "HEALTHY"
    ).sum()

    stable = (
        status == "STABLE"
    ).sum()

    recovering = (
        status == "RECOVERING"
    ).sum()

    degraded = (
        status == "DEGRADED"
    ).sum()

    critical = (
        status == "CRITICAL"
    ).sum()

    total = len(df)

    print(
        f"Healthy Recovery         : "
        f"{healthy:3d} "
        f"({healthy / total * 100:.2f}%)"
    )

    print(
        f"Stable Recovery          : "
        f"{stable:3d} "
        f"({stable / total * 100:.2f}%)"
    )

    print(
        f"Recovering               : "
        f"{recovering:3d} "
        f"({recovering / total * 100:.2f}%)"
    )

    print(
        f"Degraded Recovery        : "
        f"{degraded:3d} "
        f"({degraded / total * 100:.2f}%)"
    )

    print(
        f"Critical Recovery        : "
        f"{critical:3d} "
        f"({critical / total * 100:.2f}%)"
    )


# ==========================================================
# OVERALL FRAMEWORK SCORE
# ==========================================================

overall_score = (
    average_atc +
    average_macs +
    average_pti +
    average_recovery
) / 4


print("\n" + "=" * 70)

print(
    f"Overall Framework Score : "
    f"{overall_score:.2f} / 100"
)


# ==========================================================
# SAVE RESULTS
# ==========================================================

performance_data = {

    "Dataset":
        INPUT_FILE,

    "Total Records":
        len(df),

    "Average ATC":
        round(average_atc, 2),

    "Average MACS":
        round(average_macs, 2),

    "Average PTI":
        round(average_pti, 2),

    "Average Recovery":
        round(average_recovery, 2),

    "Overall Framework Score":
        round(overall_score, 2)
}


performance_df = pd.DataFrame(
    [performance_data]
)


performance_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"\nResults saved to: {OUTPUT_FILE}"
)

print("=" * 70)