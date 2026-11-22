# ==========================================================
# PHARMACEUTICAL BLOCKCHAIN FRAMEWORK
# MATHEMATICAL & LOGIC VALIDATION
# ==========================================================

import pandas as pd


# ==========================================================
# SETTINGS
# ==========================================================

INPUT_FILE = "experiment_results.csv"


# ==========================================================
# LOAD DATA
# ==========================================================

print("\n" + "=" * 70)
print("       PHARMACEUTICAL BLOCKCHAIN FRAMEWORK VALIDATION")
print("=" * 70)

try:
    df = pd.read_csv(INPUT_FILE)

except FileNotFoundError:
    print("\nERROR: experiment_results.csv was not found.")
    exit()

print(f"\nLoaded {len(df)} experimental transactions.")


# ==========================================================
# HELPER
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
# FIND COLUMNS
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

risk_col = find_column([
    "Risk",
    "Risk Level",
    "risk_level"
])

counterfeit_col = find_column([
    "Counterfeit",
    "counterfeit"
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
# VALIDATION COUNTERS
# ==========================================================

total_checks = 0
passed_checks = 0
failed_checks = 0


def check(condition, message):

    global total_checks
    global passed_checks
    global failed_checks

    total_checks += 1

    if condition:

        passed_checks += 1

        print(f"[PASS] {message}")

    else:

        failed_checks += 1

        print(f"[FAIL] {message}")


# ==========================================================
# 1. SCORE RANGE VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("1. SCORE RANGE VALIDATION")
print("=" * 70)


for name, column in [
    ("ATC", atc_col),
    ("MACS", macs_col),
    ("PTI", pti_col),
    ("Recovery", recovery_col)
]:

    if column is not None:

        valid_range = (
            df[column].between(0, 100).all()
        )

        check(
            valid_range,
            f"{name} scores remain between 0 and 100"
        )


# ==========================================================
# 2. MISSING VALUE VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("2. DATA COMPLETENESS VALIDATION")
print("=" * 70)


for name, column in [
    ("ATC", atc_col),
    ("MACS", macs_col),
    ("PTI", pti_col),
    ("Recovery", recovery_col)
]:

    if column is not None:

        missing = df[column].isna().sum()

        check(
            missing == 0,
            f"{name} contains no missing values"
        )


# ==========================================================
# 3. ATC LOGIC VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("3. ATC LOGIC VALIDATION")
print("=" * 70)


if atc_col is not None:

    trusted = (
        df[atc_col] >= 70
    ).sum()

    suspicious = (
        df[atc_col] < 50
    ).sum()

    monitor = (
        (df[atc_col] >= 50) &
        (df[atc_col] < 70)
    ).sum()

    print(
        f"Trusted       : {trusted}"
    )

    print(
        f"Monitor       : {monitor}"
    )

    print(
        f"Suspicious    : {suspicious}"
    )

    check(
        trusted + monitor + suspicious == len(df),
        "Every transaction receives exactly one ATC status range"
    )


# ==========================================================
# 4. MACS LOGIC VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("4. MACS LOGIC VALIDATION")
print("=" * 70)


if macs_col is not None:

    genuine = (
        df[macs_col] >= 80
    ).sum()

    suspicious = (
        (df[macs_col] >= 60) &
        (df[macs_col] < 80)
    ).sum()

    counterfeit_risk = (
        df[macs_col] < 60
    ).sum()

    print(
        f"Genuine          : {genuine}"
    )

    print(
        f"Suspicious       : {suspicious}"
    )

    print(
        f"Counterfeit Risk : {counterfeit_risk}"
    )

    check(
        genuine +
        suspicious +
        counterfeit_risk
        == len(df),
        "Every transaction receives exactly one MACS category"
    )


# ==========================================================
# 5. PTI LOGIC VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("5. PTI LOGIC VALIDATION")
print("=" * 70)


if pti_col is not None:

    highly_trusted = (
        df[pti_col] >= 80
    ).sum()

    trusted = (
        (df[pti_col] >= 60) &
        (df[pti_col] < 80)
    ).sum()

    monitor = (
        (df[pti_col] >= 40) &
        (df[pti_col] < 60)
    ).sum()

    low_trust = (
        df[pti_col] < 40
    ).sum()

    print(
        f"Highly Trusted : {highly_trusted}"
    )

    print(
        f"Trusted        : {trusted}"
    )

    print(
        f"Monitor        : {monitor}"
    )

    print(
        f"Low Trust      : {low_trust}"
    )

    check(
        highly_trusted +
        trusted +
        monitor +
        low_trust
        == len(df),
        "Every transaction receives exactly one PTI category"
    )


# ==========================================================
# 6. RISK LOGIC VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("6. RISK LOGIC VALIDATION")
print("=" * 70)


if risk_col is not None:

    valid_risks = [
        "LOW",
        "MEDIUM",
        "HIGH"
    ]

    actual_risks = (
        df[risk_col]
        .astype(str)
        .str.upper()
        .unique()
    )

    invalid_risks = [
        risk
        for risk in actual_risks
        if risk not in valid_risks
    ]

    check(
        len(invalid_risks) == 0,
        "All risk levels are LOW, MEDIUM or HIGH"
    )


# ==========================================================
# 7. COUNTERFEIT LOGIC VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("7. COUNTERFEIT LOGIC VALIDATION")
print("=" * 70)


if counterfeit_col is not None:

    valid_values = [
        "YES",
        "NO",
        "POSSIBLE"
    ]

    actual_values = (
        df[counterfeit_col]
        .astype(str)
        .str.upper()
        .unique()
    )

    invalid_values = [
        value
        for value in actual_values
        if value not in valid_values
    ]

    check(
        len(invalid_values) == 0,
        "Counterfeit classification uses valid categories"
    )


# ==========================================================
# 8. RECOVERY SCORE VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("8. SELF-HEALING VALIDATION")
print("=" * 70)


if recovery_col is not None:

    healthy = (
        df[recovery_col] >= 80
    ).sum()

    stable = (
        (df[recovery_col] >= 60) &
        (df[recovery_col] < 80)
    ).sum()

    degraded = (
        (df[recovery_col] >= 40) &
        (df[recovery_col] < 60)
    ).sum()

    critical = (
        df[recovery_col] < 40
    ).sum()

    check(
        healthy +
        stable +
        degraded +
        critical
        == len(df),
        "Every transaction receives exactly one recovery category"
    )

    check(
        df[recovery_col].between(0, 100).all(),
        "Recovery scores remain between 0 and 100"
    )


# ==========================================================
# 9. PIPELINE CONSISTENCY
# ==========================================================

print("\n" + "=" * 70)
print("9. PIPELINE CONSISTENCY")
print("=" * 70)


required_columns = [
    atc_col,
    macs_col,
    pti_col,
    recovery_col
]

check(
    all(
        column is not None
        for column in required_columns
    ),
    "ATC → MACS → PTI → Self-Healing data pipeline is complete"
)


# ==========================================================
# 10. STATISTICAL CONSISTENCY
# ==========================================================

print("\n" + "=" * 70)
print("10. STATISTICAL CONSISTENCY")
print("=" * 70)


if atc_col and macs_col and pti_col and recovery_col:

    means = {
        "ATC": df[atc_col].mean(),
        "MACS": df[macs_col].mean(),
        "PTI": df[pti_col].mean(),
        "Recovery": df[recovery_col].mean()
    }

    for name, value in means.items():

        print(
            f"{name:<10}: {value:.2f}"
        )

    check(
        all(
            0 <= value <= 100
            for value in means.values()
        ),
        "All average scores remain mathematically valid"
    )


# ==========================================================
# FINAL VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("                 VALIDATION SUMMARY")
print("=" * 70)

print(
    f"\nTotal Checks : {total_checks}"
)

print(
    f"Passed       : {passed_checks}"
)

print(
    f"Failed       : {failed_checks}"
)


if failed_checks == 0:

    print(
        "\nVALIDATION RESULT : PASSED"
    )

    print(
        "The implemented framework is"
    )

    print(
        "mathematically and logically consistent"
    )

else:

    print(
        "\nVALIDATION RESULT : REVIEW REQUIRED"
    )

    print(
        "Some validation checks failed."
    )


print("\n" + "=" * 70)