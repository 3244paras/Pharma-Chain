# ==========================================================
# PHARMACEUTICAL BLOCKCHAIN
# MANUAL MEDICINE DATA MODE
# ==========================================================

from models.medicine import Medicine
from modules.atc import AdaptiveTrustConsensus
from modules.macs import MedicineAuthenticityConfidenceScore
from modules.pti import PharmaTrustIndex
from modules.self_healing import SelfHealing


# ==========================================================
# INITIALIZE FRAMEWORK
# ==========================================================

atc = AdaptiveTrustConsensus()
macs = MedicineAuthenticityConfidenceScore()
pti = PharmaTrustIndex()
self_healing = SelfHealing()


# ==========================================================
# ENTER MEDICINE DATA
# ==========================================================

def enter_medicine():

    print("\n" + "=" * 60)
    print("              ENTER MEDICINE DETAILS")
    print("=" * 60)

    medicine = Medicine(

        medicine_id=input(
            "Medicine ID: "
        ),

        medicine_name=input(
            "Medicine Name: "
        ),

        batch_number=input(
            "Batch Number: "
        ),

        manufacturer=input(
            "Manufacturer: "
        ),

        distributor=input(
            "Distributor: "
        ),

        wholesaler=input(
            "Wholesaler: "
        ),

        pharmacy=input(
            "Pharmacy: "
        ),

        manufacture_date=input(
            "Manufacture Date (YYYY-MM-DD): "
        ),

        expiry_date=input(
            "Expiry Date (YYYY-MM-DD): "
        ),

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
        ),

        state=input(
            "State: "
        )
    )

    return medicine


# ==========================================================
# COUNTERFEIT DETECTION
# ==========================================================

def detect_counterfeit(macs_score):

    if macs_score >= 80:

        return "NO", "LOW"

    elif macs_score >= 60:

        return "POSSIBLE", "MEDIUM"

    else:

        return "YES", "HIGH"


# ==========================================================
# DETECT PROBLEMS
# ==========================================================

def detect_problems(medicine):

    problems = []

    if not medicine.qr_verified:

        problems.append(
            "QR verification failed"
        )

    if not medicine.package_intact:

        problems.append(
            "Package integrity failed"
        )

    if not medicine.batch_verified:

        problems.append(
            "Batch verification failed"
        )

    if medicine.transport_time > 72:

        problems.append(
            "Excessive transport time"
        )

    if not (
        0 <= medicine.temperature <= 40
    ):

        problems.append(
            "Temperature outside acceptable range"
        )

    if not (
        10 <= medicine.humidity <= 80
    ):

        problems.append(
            "Humidity outside acceptable range"
        )

    return problems


# ==========================================================
# PROCESS MEDICINE
# ==========================================================

def process_medicine(medicine):

    # ------------------------------------------------------
    # ATC
    # ------------------------------------------------------

    atc_result = atc.calculate_adaptive_atc(
        medicine
    )

    atc_score = atc_result["atc_score"]

    atc_status = atc_result["status"]


    # ------------------------------------------------------
    # MACS
    # ------------------------------------------------------

    macs_score, macs_status = (
        macs.calculate_macs(
            medicine
        )
    )


    # ------------------------------------------------------
    # COUNTERFEIT
    # ------------------------------------------------------

    counterfeit, risk_level = (
        detect_counterfeit(
            macs_score
        )
    )


    # ------------------------------------------------------
    # COMPLIANCE SCORE
    # ------------------------------------------------------

    compliance_score = 0

    if medicine.qr_verified:

        compliance_score += 35

    if medicine.package_intact:

        compliance_score += 30

    if medicine.batch_verified:

        compliance_score += 35


    # ------------------------------------------------------
    # PTI
    # ------------------------------------------------------

    pti_score, pti_status = (
        pti.calculate_pti(
            atc_score,
            macs_score,
            compliance_score,
            risk_level
        )
    )


    # ------------------------------------------------------
    # SELF-HEALING
    # ------------------------------------------------------

    healing_result = self_healing.heal(

        medicine.manufacturer,

        atc_score,

        pti_score,

        counterfeit == "YES",

        risk_level
    )


    # ------------------------------------------------------
    # PROBLEMS
    # ------------------------------------------------------

    problems = detect_problems(
        medicine
    )


    # ------------------------------------------------------
    # DISPLAY RESULTS
    # ------------------------------------------------------

    print("\n" + "=" * 60)
    print("             MEDICINE ANALYSIS")
    print("=" * 60)

    print(
        f"\nMedicine ID       : "
        f"{medicine.medicine_id}"
    )

    print(
        f"Medicine Name     : "
        f"{medicine.medicine_name}"
    )

    print(
        f"Batch Number      : "
        f"{medicine.batch_number}"
    )

    print("\n---------------- ATC ----------------")

    print(
        f"ATC Score         : "
        f"{atc_score}"
    )

    print(
        f"ATC Status        : "
        f"{atc_status}"
    )

    print("\n---------------- MACS ----------------")

    print(
        f"MACS Score        : "
        f"{macs_score}"
    )

    print(
        f"MACS Status       : "
        f"{macs_status}"
    )

    print("\n------------- COUNTERFEIT ------------")

    print(
        f"Counterfeit       : "
        f"{counterfeit}"
    )

    print(
        f"Risk Level        : "
        f"{risk_level}"
    )

    print("\n---------------- PTI -----------------")

    print(
        f"PTI Score         : "
        f"{pti_score}"
    )

    print(
        f"PTI Status        : "
        f"{pti_status}"
    )

    print("\n------------ SELF-HEALING ------------")

    print(
        f"Updated Trust     : "
        f"{healing_result['trust_score']}"
    )

    print(
        f"Updated PTI       : "
        f"{healing_result['pti_score']}"
    )

    print(
        f"Recovery Score    : "
        f"{healing_result['recovery_score']}"
    )

    print(
        f"Recovery Status   : "
        f"{healing_result['recovery_status']}"
    )

    print(
        f"Network Status    : "
        f"{healing_result['status']}"
    )


    # ------------------------------------------------------
    # PROBLEMS
    # ------------------------------------------------------

    print("\n----------- DETECTED PROBLEMS ---------")

    if problems:

        for problem in problems:

            print(
                f"- {problem}"
            )

    else:

        print("None")


    print("\n" + "=" * 60)

    return {

        "Medicine ID":
            medicine.medicine_id,

        "Medicine Name":
            medicine.medicine_name,

        "Batch Number":
            medicine.batch_number,

        "ATC":
            atc_score,

        "ATC Status":
            atc_status,

        "MACS":
            macs_score,

        "MACS Status":
            macs_status,

        "Counterfeit":
            counterfeit,

        "Risk":
            risk_level,

        "PTI":
            pti_score,

        "PTI Status":
            pti_status,

        "Updated Trust":
            healing_result["trust_score"],

        "Updated PTI":
            healing_result["pti_score"],

        "Recovery":
            healing_result["recovery_score"],

        "Recovery Status":
            healing_result["recovery_status"],

        "Network Status":
            healing_result["status"],

        "Detected Problems":
            "; ".join(problems)
    }


# ==========================================================
# MAIN PROGRAM
# ==========================================================

def main():

    print("\n" + "=" * 60)
    print("       MANUAL PHARMACEUTICAL DATA ANALYSIS")
    print("=" * 60)

    results = []

    try:

        number = int(
            input(
                "\nHow many medicines do you want to enter? "
            )
        )

    except ValueError:

        print(
            "\nPlease enter a valid number."
        )

        return


    if number <= 0:

        print(
            "\nNumber of medicines must be greater than 0."
        )

        return


    for i in range(number):

        print(
            f"\n\nMEDICINE {i + 1} OF {number}"
        )

        try:

            medicine = enter_medicine()

            # --------------------------------------------------
            # Validate medicine
            # --------------------------------------------------

            valid, message = medicine.validate()

            if not valid:

                print(
                    f"\nValidation Error: {message}"
                )

                continue


            # --------------------------------------------------
            # Process medicine
            # --------------------------------------------------

            result = process_medicine(
                medicine
            )

            results.append(result)


        except ValueError:

            print(
                "\nInvalid numeric value entered."
            )

            print(
                "This medicine was skipped."
            )


        except Exception as error:

            print(
                f"\nError processing medicine: {error}"
            )


    # ======================================================
    # SAVE MANUAL RESULTS
    # ======================================================

    if results:

        import pandas as pd

        output_file = (
            "manual_results.csv"
        )

        results_df = pd.DataFrame(
            results
        )

        results_df.to_csv(
            output_file,
            index=False
        )

        print("\n" + "=" * 60)

        print(
            f"Manual results saved to: "
            f"{output_file}"
        )

        print(
            f"Successfully processed: "
            f"{len(results)}"
        )

        print("=" * 60)

    else:

        print(
            "\nNo valid medicines were processed."
        )


# ==========================================================
# PROGRAM START
# ==========================================================

if __name__ == "__main__":

    main()