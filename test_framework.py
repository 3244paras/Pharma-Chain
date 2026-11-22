"""
==============================================================
PHARMACEUTICAL BLOCKCHAIN FRAMEWORK
MULTI-TRANSACTION TESTING
==============================================================

Tests:
    1. ATC
    2. MACS
    3. Counterfeit Detection
    4. PTI
    5. Self-Healing

This test does NOT modify the blockchain.
==============================================================
"""

from models.medicine import Medicine

from modules.atc import AdaptiveTrustConsensus

from modules.macs import (
    MedicineAuthenticityConfidenceScore
)

from modules.pti import PharmaTrustIndex

from modules.self_healing import SelfHealing


# ==============================================================
# COUNTERFEIT DETECTION
# ==============================================================

def counterfeit_detection(medicine, macs_score):

    problems = []

    # QR verification
    if not medicine.qr_verified:
        problems.append("QR verification failed")

    # Package integrity
    if not medicine.package_intact:
        problems.append("Package integrity failed")

    # Batch verification
    if not medicine.batch_verified:
        problems.append("Batch verification failed")

    # Transport time
    if medicine.transport_time > 48:
        problems.append("Excessive transport time")

    # ----------------------------------------------------------
    # Determine counterfeit risk
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

    # ----------------------------------------------------------
    # MACS override
    # ----------------------------------------------------------

    if macs_score < 50:

        counterfeit = "YES"
        risk_level = "HIGH"

    return counterfeit, risk_level, problems


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
# CREATE TEST MEDICINE
# ==============================================================

def create_medicine(
    medicine_id,
    medicine_name,
    qr_verified,
    package_intact,
    batch_verified,
    temperature,
    humidity,
    transport_time
):

    return Medicine(

        medicine_id=medicine_id,

        medicine_name=medicine_name,

        batch_number="BATCH-" + medicine_id,

        manufacturer="Test Pharma",

        distributor="Test Distributor",

        wholesaler="Test Wholesaler",

        pharmacy="Test Pharmacy",

        manufacture_date="2026-01-01",

        expiry_date="2028-01-01",

        temperature=temperature,

        humidity=humidity,

        qr_verified=qr_verified,

        package_intact=package_intact,

        batch_verified=batch_verified,

        transport_time=transport_time,

        city="Bengaluru",

        state="Karnataka"
    )


# ==============================================================
# RUN ONE TEST
# ==============================================================

def run_test(
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

    macs_score, macs_status = macs.calculate_macs(
        medicine
    )

    # ----------------------------------------------------------
    # COUNTERFEIT DETECTION
    # ----------------------------------------------------------

    (
        counterfeit,
        risk_level,
        problems
    ) = counterfeit_detection(
        medicine,
        macs_score
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
    # Return results
    # ----------------------------------------------------------

    return {

        "medicine_id": medicine.medicine_id,

        "atc": atc_score,

        "atc_status": atc_result["status"],

        "macs": macs_score,

        "macs_status": macs_status,

        "pti": pti_score,

        "pti_status": pti_status,

        "counterfeit": counterfeit,

        "risk": risk_level,

        "trust_after_healing":
            healing_result["trust_score"],

        "pti_after_healing":
            healing_result["pti_score"],

        "recovery_score":
            healing_result["recovery_score"],

        "recovery_status":
            healing_result["recovery_status"],

        "network_status":
            healing_result["status"],

        "problems": problems
    }


# ==============================================================
# DISPLAY SUMMARY
# ==============================================================

def display_results(results):

    print("\n")

    print("=" * 110)

    print(
        "                 MULTI-TRANSACTION TEST RESULTS"
    )

    print("=" * 110)

    print(
        f"{'ID':<10}"
        f"{'ATC':<10}"
        f"{'MACS':<10}"
        f"{'PTI':<10}"
        f"{'Risk':<12}"
        f"{'Trust':<12}"
        f"{'Recovery':<12}"
    )

    print("-" * 110)

    for result in results:

        print(
            f"{result['medicine_id']:<10}"
            f"{result['atc']:<10.2f}"
            f"{result['macs']:<10.2f}"
            f"{result['pti']:<10.2f}"
            f"{result['risk']:<12}"
            f"{result['trust_after_healing']:<12.2f}"
            f"{result['recovery_score']:<12.2f}"
        )

    print("=" * 110)


# ==============================================================
# DISPLAY DETAILED RESULTS
# ==============================================================

def display_detailed_results(results):

    print("\n")

    print("=" * 70)

    print(
        "                    DETAILED ANALYSIS"
    )

    print("=" * 70)

    for result in results:

        print("\n" + "-" * 70)

        print(
            f"Medicine ID       : "
            f"{result['medicine_id']}"
        )

        print(
            f"ATC Score         : "
            f"{result['atc']}"
        )

        print(
            f"ATC Status        : "
            f"{result['atc_status']}"
        )

        print(
            f"MACS Score        : "
            f"{result['macs']}"
        )

        print(
            f"MACS Status       : "
            f"{result['macs_status']}"
        )

        print(
            f"PTI Score         : "
            f"{result['pti']}"
        )

        print(
            f"PTI Status        : "
            f"{result['pti_status']}"
        )

        print(
            f"Counterfeit       : "
            f"{result['counterfeit']}"
        )

        print(
            f"Risk Level        : "
            f"{result['risk']}"
        )

        print(
            f"Updated Trust     : "
            f"{result['trust_after_healing']}"
        )

        print(
            f"Updated PTI       : "
            f"{result['pti_after_healing']}"
        )

        print(
            f"Recovery Score    : "
            f"{result['recovery_score']}"
        )

        print(
            f"Recovery Status   : "
            f"{result['recovery_status']}"
        )

        print(
            f"Network Status    : "
            f"{result['network_status']}"
        )

        if result["problems"]:

            print("\nDetected Problems:")

            for problem in result["problems"]:

                print(
                    f"  - {problem}"
                )

        else:

            print(
                "\nDetected Problems: None"
            )

    print("\n" + "=" * 70)


# ==============================================================
# MAIN TEST PROGRAM
# ==============================================================

def main():

    print("\n")

    print("=" * 70)

    print(
        "       PHARMACEUTICAL BLOCKCHAIN FRAMEWORK TEST"
    )

    print("=" * 70)

    print(
        "\nTesting multiple medicine transactions..."
    )

    # ----------------------------------------------------------
    # CREATE MODULE OBJECTS
    # ----------------------------------------------------------

    atc = AdaptiveTrustConsensus()

    macs = MedicineAuthenticityConfidenceScore()

    pti = PharmaTrustIndex()

    healing = SelfHealing()

    # ----------------------------------------------------------
    # TEST MEDICINES
    # ----------------------------------------------------------

    medicines = [

        # ======================================================
        # TEST 1 — FULLY VERIFIED
        # ======================================================

        create_medicine(

            "MED001",
            "Paracetamol",

            True,
            True,
            True,

            25,
            50,
            12
        ),

        # ======================================================
        # TEST 2 — VERIFIED, LONGER TRANSPORT
        # ======================================================

        create_medicine(

            "MED002",
            "Amoxicillin",

            True,
            True,
            True,

            28,
            60,
            36
        ),

        # ======================================================
        # TEST 3 — QR FAILURE
        # ======================================================

        create_medicine(

            "MED003",
            "Insulin",

            False,
            True,
            True,

            25,
            50,
            24
        ),

        # ======================================================
        # TEST 4 — MULTIPLE FAILURES
        # ======================================================

        create_medicine(

            "MED004",
            "Azithromycin",

            False,
            False,
            True,

            35,
            75,
            72
        ),

        # ======================================================
        # TEST 5 — HIGH RISK
        # ======================================================

        create_medicine(

            "MED005",
            "Test Medicine",

            False,
            False,
            False,

            45,
            90,
            100
        )
    ]

    # ----------------------------------------------------------
    # RUN ALL TESTS
    # ----------------------------------------------------------

    results = []

    for medicine in medicines:

        result = run_test(

            medicine,

            atc,

            macs,

            pti,

            healing
        )

        results.append(result)

    # ----------------------------------------------------------
    # SUMMARY
    # ----------------------------------------------------------

    display_results(results)

    # ----------------------------------------------------------
    # DETAILED RESULTS
    # ----------------------------------------------------------

    display_detailed_results(results)

    # ----------------------------------------------------------
    # COMPLETION MESSAGE
    # ----------------------------------------------------------

    print("\n")

    print("=" * 70)

    print(
        "                 TESTING COMPLETED"
    )

    print("=" * 70)

    print(
        f"\nTotal medicines tested: "
        f"{len(results)}"
    )

    print(
        "\nFramework components tested:"
    )

    print("  ✓ Adaptive Trust Consensus (ATC)")
    print("  ✓ Medicine Authenticity Confidence Score (MACS)")
    print("  ✓ Counterfeit Detection")
    print("  ✓ Pharma Trust Index (PTI)")
    print("  ✓ Self-Healing")

    print("=" * 70)


# ==============================================================
# PROGRAM ENTRY
# ==============================================================

if __name__ == "__main__":

    main()