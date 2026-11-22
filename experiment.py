"""
==============================================================
PHARMACEUTICAL BLOCKCHAIN FRAMEWORK
EXPERIMENTAL EVALUATION
==============================================================

Generates 100 simulated medicine transactions and evaluates:

    ATC
    MACS
    Counterfeit Detection
    PTI
    Self-Healing

Output:
    experiment_results.csv

==============================================================
"""

import random
import csv

from models.medicine import Medicine

from modules.atc import AdaptiveTrustConsensus
from modules.macs import MedicineAuthenticityConfidenceScore
from modules.pti import PharmaTrustIndex
from modules.self_healing import SelfHealing


# ==============================================================
# COUNTERFEIT DETECTION
# ==============================================================

def counterfeit_detection(medicine, macs_score):

    problems = []

    if not medicine.qr_verified:
        problems.append("QR verification failed")

    if not medicine.package_intact:
        problems.append("Package integrity failed")

    if not medicine.batch_verified:
        problems.append("Batch verification failed")

    if medicine.transport_time > 48:
        problems.append("Excessive transport time")

    # ----------------------------------------------------------
    # Risk classification
    # ----------------------------------------------------------

    if len(problems) == 0:

        counterfeit = "NO"
        risk_level = "LOW"

    elif len(problems) == 1:

        counterfeit = "POSSIBLE"
        risk_level = "MEDIUM"

    else:

        counterfeit = "YES"
        risk_level = "HIGH"

    # MACS override

    if macs_score < 50:

        counterfeit = "YES"
        risk_level = "HIGH"

    return counterfeit, risk_level


# ==============================================================
# COMPLIANCE SCORE
# ==============================================================

def calculate_compliance(medicine):

    score = 0

    if medicine.qr_verified:
        score += 35

    if medicine.package_intact:
        score += 30

    if medicine.batch_verified:
        score += 35

    return score


# ==============================================================
# CREATE RANDOM MEDICINE
# ==============================================================

def create_random_medicine(index):

    medicine_names = [
        "Paracetamol",
        "Amoxicillin",
        "Insulin",
        "Azithromycin",
        "Metformin",
        "Ibuprofen",
        "Cefixime",
        "Aspirin",
        "Doxycycline",
        "Cetirizine"
    ]

    return Medicine(

        medicine_id=f"EXP{index:03d}",

        medicine_name=random.choice(
            medicine_names
        ),

        batch_number=f"BATCH-EXP{index:03d}",

        manufacturer="Experimental Pharma",

        distributor="Experimental Distributor",

        wholesaler="Experimental Wholesaler",

        pharmacy="Experimental Pharmacy",

        manufacture_date="2026-01-01",

        expiry_date="2028-01-01",

        # Temperature range deliberately includes
        # normal and abnormal conditions.
        temperature=round(
            random.uniform(0, 45),
            2
        ),

        # Humidity includes normal and abnormal values.
        humidity=round(
            random.uniform(10, 90),
            2
        ),

        # Verification states create different
        # trust/risk conditions.
        qr_verified=random.random() < 0.85,

        package_intact=random.random() < 0.85,

        batch_verified=random.random() < 0.85,

        # Transport time between 6 and 100 hours.
        transport_time=round(
            random.uniform(6, 100),
            2
        ),

        city="Bengaluru",

        state="Karnataka"
    )


# ==============================================================
# PROCESS ONE MEDICINE
# ==============================================================

def process_medicine(
    medicine,
    atc,
    macs,
    pti,
    healing
):

    # ----------------------------------------------------------
    # ATC
    # ----------------------------------------------------------

    atc_result = atc.calculate_adaptive_atc(
        medicine
    )

    atc_score = atc_result["atc_score"]

    # ----------------------------------------------------------
    # MACS
    # ----------------------------------------------------------

    macs_score, macs_status = (
        macs.calculate_macs(
            medicine
        )
    )

    # ----------------------------------------------------------
    # COUNTERFEIT
    # ----------------------------------------------------------

    counterfeit, risk_level = (
        counterfeit_detection(
            medicine,
            macs_score
        )
    )

    # ----------------------------------------------------------
    # COMPLIANCE
    # ----------------------------------------------------------

    compliance_score = calculate_compliance(
        medicine
    )

    # ----------------------------------------------------------
    # PTI
    # ----------------------------------------------------------

    pti_score, pti_status = pti.calculate_pti(

        atc_score,

        macs_score,

        compliance_score,

        risk_level
    )

    # ----------------------------------------------------------
    # SELF-HEALING
    # ----------------------------------------------------------

    # Both YES and POSSIBLE are treated
    # as requiring adaptive response.

    counterfeit_detected = (
        counterfeit in ["YES", "POSSIBLE"]
    )

    healing_result = healing.heal(

        medicine.manufacturer,

        atc_score,

        pti_score,

        counterfeit_detected,

        risk_level
    )

    # ----------------------------------------------------------
    # RETURN EXPERIMENT RESULT
    # ----------------------------------------------------------

    return {

        "Medicine_ID":
            medicine.medicine_id,

        "Medicine_Name":
            medicine.medicine_name,

        "Temperature":
            medicine.temperature,

        "Humidity":
            medicine.humidity,

        "Transport_Time":
            medicine.transport_time,

        "QR_Verified":
            medicine.qr_verified,

        "Package_Intact":
            medicine.package_intact,

        "Batch_Verified":
            medicine.batch_verified,

        "ATC":
            atc_score,

        "ATC_Status":
            atc_result["status"],

        "MACS":
            macs_score,

        "MACS_Status":
            macs_status,

        "Counterfeit":
            counterfeit,

        "Risk_Level":
            risk_level,

        "PTI":
            pti_score,

        "PTI_Status":
            pti_status,

        "Updated_Trust":
            healing_result["trust_score"],

        "Updated_PTI":
            healing_result["pti_score"],

        "Recovery_Score":
            healing_result["recovery_score"],

        "Recovery_Status":
            healing_result["recovery_status"],

        "Network_Status":
            healing_result["status"]
    }


# ==============================================================
# SAVE CSV
# ==============================================================

def save_results(results):

    filename = "experiment_results.csv"

    if not results:
        return

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()

        writer.writerows(results)

    print(
        f"\nResults saved to: {filename}"
    )


# ==============================================================
# DISPLAY SUMMARY
# ==============================================================

def display_summary(results):

    total = len(results)

    genuine = sum(
        1
        for r in results
        if r["Counterfeit"] == "NO"
    )

    possible = sum(
        1
        for r in results
        if r["Counterfeit"] == "POSSIBLE"
    )

    counterfeit = sum(
        1
        for r in results
        if r["Counterfeit"] == "YES"
    )

    low_risk = sum(
        1
        for r in results
        if r["Risk_Level"] == "LOW"
    )

    medium_risk = sum(
        1
        for r in results
        if r["Risk_Level"] == "MEDIUM"
    )

    high_risk = sum(
        1
        for r in results
        if r["Risk_Level"] == "HIGH"
    )

    isolated = sum(
        1
        for r in results
        if "Isolated" in r["Network_Status"]
    )

    monitored = sum(
        1
        for r in results
        if "Monitoring" in r["Network_Status"]
    )

    average_atc = sum(
        r["ATC"]
        for r in results
    ) / total

    average_macs = sum(
        r["MACS"]
        for r in results
    ) / total

    average_pti = sum(
        r["PTI"]
        for r in results
    ) / total

    average_recovery = sum(
        r["Recovery_Score"]
        for r in results
    ) / total

    print("\n")
    print("=" * 65)
    print("             EXPERIMENTAL RESULTS SUMMARY")
    print("=" * 65)

    print(
        f"Total Transactions       : {total}"
    )

    print(
        f"Genuine                  : {genuine}"
    )

    print(
        f"Possible Counterfeit     : {possible}"
    )

    print(
        f"Counterfeit Risk         : {counterfeit}"
    )

    print("-" * 65)

    print(
        f"Low Risk                 : {low_risk}"
    )

    print(
        f"Medium Risk              : {medium_risk}"
    )

    print(
        f"High Risk                : {high_risk}"
    )

    print("-" * 65)

    print(
        f"Average ATC Score        : "
        f"{average_atc:.2f}"
    )

    print(
        f"Average MACS Score       : "
        f"{average_macs:.2f}"
    )

    print(
        f"Average PTI Score        : "
        f"{average_pti:.2f}"
    )

    print(
        f"Average Recovery Score   : "
        f"{average_recovery:.2f}"
    )

    print("-" * 65)

    print(
        f"Participants Isolated    : "
        f"{isolated}"
    )

    print(
        f"Participants Monitored  : "
        f"{monitored}"
    )

    print("=" * 65)


# ==============================================================
# DISPLAY SAMPLE RESULTS
# ==============================================================

def display_sample(results):

    print("\n")
    print("=" * 100)
    print("                  FIRST 10 EXPERIMENTAL RESULTS")
    print("=" * 100)

    print(
        f"{'ID':<10}"
        f"{'ATC':<10}"
        f"{'MACS':<10}"
        f"{'PTI':<10}"
        f"{'Risk':<12}"
        f"{'Recovery':<12}"
    )

    print("-" * 100)

    for result in results[:10]:

        print(
            f"{result['Medicine_ID']:<10}"
            f"{result['ATC']:<10.2f}"
            f"{result['MACS']:<10.2f}"
            f"{result['PTI']:<10.2f}"
            f"{result['Risk_Level']:<12}"
            f"{result['Recovery_Score']:<12.2f}"
        )

    print("=" * 100)


# ==============================================================
# MAIN
# ==============================================================

def main():

    print("\n")
    print("=" * 65)
    print("     PHARMACEUTICAL BLOCKCHAIN EXPERIMENT")
    print("=" * 65)

    print(
        "\nGenerating 100 simulated medicine transactions..."
    )

    # ----------------------------------------------------------
    # Fixed seed
    # ----------------------------------------------------------
    # This makes the experiment reproducible.
    # Running the program again produces the same dataset.

    random.seed(42)

    # ----------------------------------------------------------
    # Create modules
    # ----------------------------------------------------------

    atc = AdaptiveTrustConsensus()

    macs = MedicineAuthenticityConfidenceScore()

    pti = PharmaTrustIndex()

    healing = SelfHealing()

    # ----------------------------------------------------------
    # Generate and process medicines
    # ----------------------------------------------------------

    results = []

    for i in range(1, 101):

        medicine = create_random_medicine(i)

        result = process_medicine(

            medicine,

            atc,

            macs,

            pti,

            healing
        )

        results.append(result)

    # ----------------------------------------------------------
    # Display
    # ----------------------------------------------------------

    display_summary(results)

    display_sample(results)

    # ----------------------------------------------------------
    # Save
    # ----------------------------------------------------------

    save_results(results)

    print("\n")
    print("=" * 65)
    print("             EXPERIMENT COMPLETED")
    print("=" * 65)


# ==============================================================
# PROGRAM ENTRY
# ==============================================================

if __name__ == "__main__":
    main()