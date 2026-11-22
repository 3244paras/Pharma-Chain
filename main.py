"""
==============================================================
PHARMACEUTICAL BLOCKCHAIN SYSTEM
==============================================================

Features:
    - Pharmaceutical Blockchain
    - Medicine Validation
    - Adaptive Trust Consensus (ATC)
    - Medicine Authenticity Confidence Score (MACS)
    - Counterfeit Detection
    - Pharma Trust Index (PTI)
    - Self-Healing
    - SQLite Database Storage
    - Reusable Medicine Processing Function
==============================================================
"""

from models.medicine import Medicine
from modules.blockchain import Blockchain
from modules.atc import AdaptiveTrustConsensus
from modules.macs import MedicineAuthenticityConfidenceScore
from modules.pti import PharmaTrustIndex
from modules.self_healing import SelfHealing

# Database module
from database import save_transaction


# ==============================================================
# ADD MEDICINE
# ==============================================================

def add_medicine():

    print("\n" + "=" * 60)
    print("                 ENTER MEDICINE DETAILS")
    print("=" * 60)

    try:

        medicine = Medicine(

            medicine_id=input(
                "Medicine ID: "
            ).strip(),

            medicine_name=input(
                "Medicine Name: "
            ).strip(),

            batch_number=input(
                "Batch Number: "
            ).strip(),

            manufacturer=input(
                "Manufacturer: "
            ).strip(),

            distributor=input(
                "Distributor: "
            ).strip(),

            wholesaler=input(
                "Wholesaler: "
            ).strip(),

            pharmacy=input(
                "Pharmacy: "
            ).strip(),

            manufacture_date=input(
                "Manufacture Date (YYYY-MM-DD): "
            ).strip(),

            expiry_date=input(
                "Expiry Date (YYYY-MM-DD): "
            ).strip(),

            temperature=float(
                input("Temperature: ")
            ),

            humidity=float(
                input("Humidity: ")
            ),

            qr_verified=input(
                "QR Verified (True/False): "
            ).strip().lower() == "true",

            package_intact=input(
                "Package Intact (True/False): "
            ).strip().lower() == "true",

            batch_verified=input(
                "Batch Verified (True/False): "
            ).strip().lower() == "true",

            transport_time=float(
                input("Transport Time (hours): ")
            ),

            city=input(
                "City: "
            ).strip(),

            state=input(
                "State: "
            ).strip()
        )

    except ValueError:

        print("\nInvalid numeric value entered.")

        print(
            "Please enter valid numbers for "
            "temperature, humidity and transport time."
        )

        return None

    # ----------------------------------------------------------
    # MEDICINE VALIDATION
    # ----------------------------------------------------------

    valid, message = medicine.validate()

    if not valid:

        print("\nMedicine Validation Failed!")
        print("Reason:", message)

        return None

    print("\nMedicine validation successful.")

    return medicine


# ==============================================================
# ATC
# ==============================================================

def calculate_atc(medicine):

    atc = AdaptiveTrustConsensus()

    result = atc.calculate_adaptive_atc(
        medicine
    )

    return result


# ==============================================================
# MACS
# ==============================================================

def calculate_macs(medicine):

    macs = MedicineAuthenticityConfidenceScore()

    score, status = macs.calculate_macs(
        medicine
    )

    return score, status


# ==============================================================
# COUNTERFEIT DETECTION
# ==============================================================

def counterfeit_detection(
    medicine,
    macs_score
):

    problems = []

    # ----------------------------------------------------------
    # QR VERIFICATION
    # ----------------------------------------------------------

    if not medicine.qr_verified:

        problems.append(
            "QR verification failed"
        )

    # ----------------------------------------------------------
    # PACKAGE INTEGRITY
    # ----------------------------------------------------------

    if not medicine.package_intact:

        problems.append(
            "Package integrity failed"
        )

    # ----------------------------------------------------------
    # BATCH VERIFICATION
    # ----------------------------------------------------------

    if not medicine.batch_verified:

        problems.append(
            "Batch verification failed"
        )

    # ----------------------------------------------------------
    # TRANSPORT TIME
    # ----------------------------------------------------------

    if medicine.transport_time > 48:

        problems.append(
            "Excessive transport time"
        )

    # ----------------------------------------------------------
    # DETERMINE RISK
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
    # MACS OVERRIDE
    # ----------------------------------------------------------

    if macs_score < 50:

        counterfeit = "YES"
        risk_level = "HIGH"

    return (
        counterfeit,
        risk_level,
        problems
    )


# ==============================================================
# PTI
# ==============================================================

def calculate_pti(
    atc_score,
    macs_score,
    medicine,
    counterfeit_risk
):

    # ----------------------------------------------------------
    # COMPLIANCE SCORE
    # ----------------------------------------------------------

    compliance_score = 0

    if medicine.qr_verified:

        compliance_score += 35

    if medicine.package_intact:

        compliance_score += 30

    if medicine.batch_verified:

        compliance_score += 35

    # ----------------------------------------------------------
    # PTI MODULE
    # ----------------------------------------------------------

    pti = PharmaTrustIndex()

    score, status = pti.calculate_pti(

        atc_score,

        macs_score,

        compliance_score,

        counterfeit_risk
    )

    return score, status


# ==============================================================
# SELF-HEALING
# ==============================================================

def calculate_self_healing(
    participant_name,
    atc_score,
    pti_score,
    counterfeit,
    risk_level
):

    healing = SelfHealing()

    # SelfHealing expects Boolean
    # True = counterfeit detected
    # False = no counterfeit detected

    counterfeit_detected = (
        counterfeit == "YES"
    )

    result = healing.heal(

        participant_name,

        atc_score,

        pti_score,

        counterfeit_detected,

        risk_level
    )

    return result


# ==============================================================
# PROCESS COMPLETE MEDICINE
# ==============================================================

def process_medicine(
    medicine,
    blockchain=None,
    save_to_database=True
):
    """
    Complete pharmaceutical verification pipeline.

    Flow:

        Medicine
            ↓
        Validation
            ↓
        ATC
            ↓
        MACS
            ↓
        Counterfeit Detection
            ↓
        PTI
            ↓
        Self-Healing
            ↓
        Database
    """

    # ----------------------------------------------------------
    # MEDICINE VALIDATION
    # ----------------------------------------------------------

    valid, message = medicine.validate()

    if not valid:

        return {
            "success": False,
            "error": message
        }

    # ----------------------------------------------------------
    # ATC
    # ----------------------------------------------------------

    atc_result = calculate_atc(
        medicine
    )

    atc_score = atc_result["atc_score"]

    # ----------------------------------------------------------
    # MACS
    # ----------------------------------------------------------

    macs_score, macs_status = calculate_macs(
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
    # PTI
    # ----------------------------------------------------------

    pti_score, pti_status = calculate_pti(

        atc_score,

        macs_score,

        medicine,

        risk_level
    )

    # ----------------------------------------------------------
    # SELF-HEALING
    # ----------------------------------------------------------

    healing_result = calculate_self_healing(

        medicine.manufacturer,

        atc_score,

        pti_score,

        counterfeit,

        risk_level
    )

    # ----------------------------------------------------------
    # BLOCKCHAIN
    # ----------------------------------------------------------

    if blockchain is not None:

        blockchain.add_block(
            medicine
        )

    # ----------------------------------------------------------
    # COMPLETE RESULT
    # ----------------------------------------------------------

    result = {

        "success": True,

        # ------------------------------------------------------
        # MEDICINE INFORMATION
        # ------------------------------------------------------

        "medicine_id":
            medicine.medicine_id,

        "medicine_name":
            medicine.medicine_name,

        "batch_number":
            medicine.batch_number,

        "manufacturer":
            medicine.manufacturer,

        "distributor":
            medicine.distributor,

        "wholesaler":
            medicine.wholesaler,

        "pharmacy":
            medicine.pharmacy,

        "city":
            medicine.city,

        "state":
            medicine.state,

        # ------------------------------------------------------
        # INPUT CONDITIONS
        # ------------------------------------------------------

        "temperature":
            medicine.temperature,

        "humidity":
            medicine.humidity,

        "transport_time":
            medicine.transport_time,

        "qr_verified":
            medicine.qr_verified,

        "package_intact":
            medicine.package_intact,

        "batch_verified":
            medicine.batch_verified,

        # ------------------------------------------------------
        # ATC
        # ------------------------------------------------------

        "atc":
            atc_score,

        "atc_status":
            atc_result["status"],

        "medicine_trust":
            atc_result["medicine_trust"],

        "success_rate":
            atc_result["success_rate"],

        "medicine_integrity":
            atc_result["medicine_integrity"],

        "compliance_history":
            atc_result["compliance_history"],

        # ------------------------------------------------------
        # MACS
        # ------------------------------------------------------

        "macs":
            macs_score,

        "macs_status":
            macs_status,

        # ------------------------------------------------------
        # COUNTERFEIT
        # ------------------------------------------------------

        "counterfeit":
            counterfeit,

        "risk_level":
            risk_level,

        "detected_problems":
            problems,

        # ------------------------------------------------------
        # PTI
        # ------------------------------------------------------

        "pti":
            pti_score,

        "pti_status":
            pti_status,

        # ------------------------------------------------------
        # SELF-HEALING
        # ------------------------------------------------------

        "updated_trust":
            healing_result["trust_score"],

        "updated_pti":
            healing_result["pti_score"],

        "recovery":
            healing_result["recovery_score"],

        "recovery_status":
            healing_result["recovery_status"],

        "network_status":
            healing_result["status"]
    }

    # ----------------------------------------------------------
    # SAVE TO SQLITE DATABASE
    # ----------------------------------------------------------

    if save_to_database:

        try:

            save_transaction(
                result
            )

            result["database_saved"] = True

        except Exception as error:

            result["database_saved"] = False

            result["database_error"] = str(
                error
            )

    else:

        result["database_saved"] = False

    return result


# ==============================================================
# DISPLAY ATC
# ==============================================================

def display_atc(result):

    print("\n" + "=" * 60)

    print(
        "             ADAPTIVE TRUST CONSENSUS (ATC)"
    )

    print("=" * 60)

    print(
        f"Medicine Trust       : "
        f"{result['medicine_trust']}"
    )

    print(
        f"Success Rate         : "
        f"{result['success_rate']}"
    )

    print(
        f"Medicine Integrity   : "
        f"{result['medicine_integrity']}"
    )

    print(
        f"Compliance History   : "
        f"{result['compliance_history']}"
    )

    print("-" * 60)

    print(
        f"ATC Score             : "
        f"{result['atc_score']}"
    )

    print(
        f"Status                : "
        f"{result['status']}"
    )

    print("=" * 60)


# ==============================================================
# DISPLAY MACS
# ==============================================================

def display_macs(
    score,
    status
):

    print("\n" + "=" * 60)

    print(
        "       MEDICINE AUTHENTICITY CONFIDENCE SCORE (MACS)"
    )

    print("=" * 60)

    print(
        f"MACS Score            : {score}"
    )

    print(
        f"Status                : {status}"
    )

    print("=" * 60)


# ==============================================================
# DISPLAY COUNTERFEIT
# ==============================================================

def display_counterfeit(
    counterfeit,
    risk_level,
    problems
):

    print("\n" + "=" * 60)

    print(
        "                 COUNTERFEIT DETECTION"
    )

    print("=" * 60)

    print(
        f"Counterfeit           : "
        f"{counterfeit}"
    )

    print(
        f"Risk Level            : "
        f"{risk_level}"
    )

    if problems:

        print("\nDetected Issues:")

        for problem in problems:

            print(
                f" - {problem}"
            )

    else:

        print(
            "\nNo counterfeit indicators detected."
        )

    print("=" * 60)


# ==============================================================
# DISPLAY PTI
# ==============================================================

def display_pti(
    score,
    status
):

    print("\n" + "=" * 60)

    print(
        "                PHARMA TRUST INDEX (PTI)"
    )

    print("=" * 60)

    print(
        f"PTI Score             : {score}"
    )

    print(
        f"Status                : {status}"
    )

    print("=" * 60)


# ==============================================================
# DISPLAY SELF-HEALING
# ==============================================================

def display_self_healing(result):

    print("\n" + "=" * 60)

    print(
        "                    SELF-HEALING"
    )

    print("=" * 60)

    print(
        f"Updated Trust Score   : "
        f"{result['trust_score']}"
    )

    print(
        f"Updated PTI           : "
        f"{result['pti_score']}"
    )

    print(
        f"Recovery Score        : "
        f"{result['recovery_score']}"
    )

    print(
        f"Recovery Status       : "
        f"{result['recovery_status']}"
    )

    print(
        f"Network Status        : "
        f"{result['status']}"
    )

    print("=" * 60)


# ==============================================================
# DISPLAY COMPLETE RESULT
# ==============================================================

def display_complete_result(result):

    if not result.get("success", False):

        print("\nVerification failed.")

        print(
            "Reason:",
            result.get("error", "Unknown error")
        )

        return

    print("\n")
    print("=" * 70)
    print("              MEDICINE VERIFICATION RESULT")
    print("=" * 70)

    print(
        f"Medicine ID           : "
        f"{result['medicine_id']}"
    )

    print(
        f"Medicine Name         : "
        f"{result['medicine_name']}"
    )

    print(
        f"Batch Number          : "
        f"{result['batch_number']}"
    )

    print("=" * 70)

    display_atc({
        "medicine_trust":
            result["medicine_trust"],

        "success_rate":
            result["success_rate"],

        "medicine_integrity":
            result["medicine_integrity"],

        "compliance_history":
            result["compliance_history"],

        "atc_score":
            result["atc"],

        "status":
            result["atc_status"]
    })

    display_macs(
        result["macs"],
        result["macs_status"]
    )

    display_counterfeit(
        result["counterfeit"],
        result["risk_level"],
        result["detected_problems"]
    )

    display_pti(
        result["pti"],
        result["pti_status"]
    )

    display_self_healing({

        "trust_score":
            result["updated_trust"],

        "pti_score":
            result["updated_pti"],

        "recovery_score":
            result["recovery"],

        "recovery_status":
            result["recovery_status"],

        "status":
            result["network_status"]
    })

    print(
        f"\nDatabase Saved      : "
        f"{'YES' if result.get('database_saved') else 'NO'}"
    )

    if not result.get("database_saved"):

        if result.get("database_error"):

            print(
                "Database Error     :",
                result["database_error"]
            )

    print("=" * 70)


# ==============================================================
# MAIN PROGRAM
# ==============================================================

def main():

    # ----------------------------------------------------------
    # CREATE BLOCKCHAIN
    # ----------------------------------------------------------

    blockchain = Blockchain()

    # ----------------------------------------------------------
    # MAIN MENU
    # ----------------------------------------------------------

    while True:

        print("\n")

        print("=" * 70)

        print(
            "             PHARMACEUTICAL BLOCKCHAIN SYSTEM"
        )

        print("=" * 70)

        print("1. Add Medicine")
        print("2. View Blockchain")
        print("3. Validate Blockchain")
        print("4. Exit")

        print("=" * 70)

        choice = input(
            "\nEnter your choice: "
        ).strip()

        # ======================================================
        # OPTION 1 — ADD MEDICINE
        # ======================================================

        if choice == "1":

            medicine = add_medicine()

            if medicine is None:

                continue

            # --------------------------------------------------
            # COMPLETE FRAMEWORK
            # --------------------------------------------------

            result = process_medicine(

                medicine,

                blockchain=blockchain,

                save_to_database=True
            )

            # --------------------------------------------------
            # DISPLAY COMPLETE RESULT
            # --------------------------------------------------

            display_complete_result(
                result
            )

            if result.get("success"):

                print(
                    "\nMedicine processed successfully."
                )

                print(
                    "Block added to blockchain."
                )

                if result.get("database_saved"):

                    print(
                        "Transaction saved to "
                        "pharma_database.db."
                    )

                else:

                    print(
                        "WARNING: Transaction could not "
                        "be saved to the database."
                    )

        # ======================================================
        # OPTION 2 — VIEW BLOCKCHAIN
        # ======================================================

        elif choice == "2":

            blockchain.display_chain()

        # ======================================================
        # OPTION 3 — VALIDATE BLOCKCHAIN
        # ======================================================

        elif choice == "3":

            print(
                "\nChecking blockchain integrity..."
            )

            if blockchain.is_valid():

                print(
                    "\nBlockchain is VALID."
                )

                print(
                    "No tampering detected."
                )

            else:

                print(
                    "\nBlockchain has been TAMPERED!"
                )

                print(
                    "Integrity verification FAILED."
                )

        # ======================================================
        # OPTION 4 — EXIT
        # ======================================================

        elif choice == "4":

            print("\n" + "=" * 60)

            print(
                "Thank you for using the"
            )

            print(
                "Pharmaceutical Blockchain System."
            )

            print("=" * 60)

            break

        # ======================================================
        # INVALID OPTION
        # ======================================================

        else:

            print(
                "\nInvalid choice."
            )

            print(
                "Please enter 1, 2, 3 or 4."
            )


# ==============================================================
# PROGRAM ENTRY POINT
# ==============================================================

if __name__ == "__main__":

    main()