import streamlit as st
import sqlite3
import pandas as pd
from datetime import date

from models.medicine import Medicine
from main import process_medicine


# ============================================================
# CONFIGURATION
# ============================================================

DATABASE = "pharma_database.db"

st.set_page_config(
    page_title="Pharma Blockchain Dashboard",
    page_icon="💊",
    layout="wide"
)


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_connection():
    return sqlite3.connect(DATABASE)


def load_transactions():
    connection = get_connection()

    query = """
    SELECT
        id,
        medicine_id,
        medicine_name,
        batch_number,
        manufacturer,
        distributor,
        pharmacy,
        temperature,
        humidity,
        transport_time,
        atc,
        atc_status,
        macs,
        macs_status,
        counterfeit,
        risk_level,
        pti,
        pti_status,
        updated_trust,
        updated_pti,
        recovery,
        recovery_status,
        network_status,
        detected_problems,
        verification_time
    FROM medicine_transactions
    ORDER BY id DESC
    """

    try:
        df = pd.read_sql_query(
            query,
            connection
        )
    finally:
        connection.close()

    return df


# ============================================================
# HEADER
# ============================================================

st.title("💊 Pharmaceutical Blockchain Dashboard")

st.caption(
    "Medicine Authenticity • Adaptive Trust • "
    "Pharma Trust • Self-Healing"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "🏠 Dashboard",
        "💊 Verify Medicine",
        "📋 Transaction History",
        "🔎 Search Medicine"
    ]
)


# ============================================================
# DASHBOARD
# ============================================================

if page == "🏠 Dashboard":

    st.header("🏥 Pharmacy Dashboard")

    try:
        df = load_transactions()

    except Exception as error:

        st.error(
            f"Database error: {error}"
        )

        st.stop()

    # --------------------------------------------------------
    # NO DATA
    # --------------------------------------------------------

    if df.empty:

        st.info(
            "No medicines have been verified yet."
        )

        st.write(
            "Go to **Verify Medicine** to add your first medicine."
        )

        st.stop()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total = len(df)

    avg_atc = df["atc"].mean()
    avg_macs = df["macs"].mean()
    avg_pti = df["pti"].mean()
    avg_recovery = df["recovery"].mean()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Medicines",
        total
    )

    col2.metric(
        "Average ATC",
        f"{avg_atc:.2f}"
    )

    col3.metric(
        "Average MACS",
        f"{avg_macs:.2f}"
    )

    col4.metric(
        "Average PTI",
        f"{avg_pti:.2f}"
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Average Recovery",
        f"{avg_recovery:.2f}"
    )

    col2.metric(
        "Genuine Medicines",
        int(
            (df["counterfeit"] == "NO").sum()
        )
    )

    col3.metric(
        "Counterfeit Risk",
        int(
            (df["counterfeit"] == "YES").sum()
        )
    )

    st.divider()

    # --------------------------------------------------------
    # RECENT TRANSACTIONS
    # --------------------------------------------------------

    st.subheader("Recent Medicine Verifications")

    display_columns = [
        "medicine_id",
        "medicine_name",
        "batch_number",
        "atc",
        "macs",
        "pti",
        "recovery",
        "risk_level"
    ]

    recent = df[display_columns].head(10)

    st.dataframe(
        recent,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # RISK DISTRIBUTION
    # --------------------------------------------------------

    st.subheader("Risk Distribution")

    risk_counts = (
        df["risk_level"]
        .value_counts()
    )

    st.bar_chart(
        risk_counts
    )

    # --------------------------------------------------------
    # SCORE COMPARISON
    # --------------------------------------------------------

    st.subheader(
        "Framework Score Comparison"
    )

    score_data = pd.DataFrame({

        "Component": [
            "ATC",
            "MACS",
            "PTI",
            "Recovery"
        ],

        "Average Score": [
            avg_atc,
            avg_macs,
            avg_pti,
            avg_recovery
        ]
    })

    st.bar_chart(
        score_data.set_index(
            "Component"
        )
    )


# ============================================================
# VERIFY MEDICINE
# ============================================================

elif page == "💊 Verify Medicine":

    st.header(
        "💊 Medicine Verification"
    )

    st.write(
        "Enter the medicine information below."
    )

    # --------------------------------------------------------
    # BASIC INFORMATION
    # --------------------------------------------------------

    st.subheader(
        "1. Medicine Information"
    )

    col1, col2 = st.columns(2)

    with col1:

        medicine_id = st.text_input(
            "Medicine ID *",
            placeholder="MED001"
        )

        medicine_name = st.text_input(
            "Medicine Name *",
            placeholder="Paracetamol"
        )

        batch_number = st.text_input(
            "Batch Number *",
            placeholder="BATCH001"
        )

        manufacturer = st.text_input(
            "Manufacturer",
            placeholder="ABC Pharma"
        )

    with col2:

        distributor = st.text_input(
            "Distributor",
            placeholder="ABC Distribution"
        )

        wholesaler = st.text_input(
            "Wholesaler",
            placeholder="ABC Wholesale"
        )

        pharmacy = st.text_input(
            "Pharmacy",
            placeholder="My Pharmacy"
        )

    # --------------------------------------------------------
    # DATES
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        manufacture_date = st.date_input(
            "Manufacture Date",
            value=date.today()
        )

    with col2:

        expiry_date = st.date_input(
            "Expiry Date"
        )

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    st.subheader(
        "2. Location"
    )

    col1, col2 = st.columns(2)

    with col1:

        city = st.text_input(
            "City",
            placeholder="Bengaluru"
        )

    with col2:

        state = st.text_input(
            "State",
            placeholder="Karnataka"
        )

    # --------------------------------------------------------
    # ENVIRONMENT
    # --------------------------------------------------------

    st.subheader(
        "3. Transport & Storage Conditions"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        temperature = st.number_input(
            "Temperature (°C)",
            min_value=-50.0,
            max_value=100.0,
            value=25.0,
            step=0.1
        )

    with col2:

        humidity = st.number_input(
            "Humidity (%)",
            min_value=0.0,
            max_value=100.0,
            value=50.0,
            step=0.1
        )

    with col3:

        transport_time = st.number_input(
            "Transport Time (hours)",
            min_value=0.0,
            max_value=1000.0,
            value=12.0,
            step=0.5
        )

    # --------------------------------------------------------
    # VERIFICATION CONDITIONS
    # --------------------------------------------------------

    st.subheader(
        "4. Verification Checks"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        qr_verified = st.checkbox(
            "QR Verified",
            value=True
        )

    with col2:

        package_intact = st.checkbox(
            "Package Intact",
            value=True
        )

    with col3:

        batch_verified = st.checkbox(
            "Batch Verified",
            value=True
        )

    st.divider()

    # --------------------------------------------------------
    # VERIFY BUTTON
    # --------------------------------------------------------

    verify = st.button(
        "🔍 VERIFY MEDICINE",
        type="primary",
        use_container_width=True
    )

    if verify:

        # ----------------------------------------------------
        # REQUIRED FIELD CHECK
        # ----------------------------------------------------

        if not medicine_id:

            st.error(
                "Medicine ID is required."
            )

            st.stop()

        if not medicine_name:

            st.error(
                "Medicine Name is required."
            )

            st.stop()

        if not batch_number:

            st.error(
                "Batch Number is required."
            )

            st.stop()

        # ----------------------------------------------------
        # CREATE MEDICINE OBJECT
        # ----------------------------------------------------

        try:

            medicine = Medicine(

                medicine_id=medicine_id,

                medicine_name=medicine_name,

                batch_number=batch_number,

                manufacturer=manufacturer,

                distributor=distributor,

                wholesaler=wholesaler,

                pharmacy=pharmacy,

                manufacture_date=
                    manufacture_date.strftime(
                        "%Y-%m-%d"
                    ),

                expiry_date=
                    expiry_date.strftime(
                        "%Y-%m-%d"
                    ),

                temperature=temperature,

                humidity=humidity,

                qr_verified=qr_verified,

                package_intact=package_intact,

                batch_verified=batch_verified,

                transport_time=transport_time,

                city=city,

                state=state
            )

        except Exception as error:

            st.error(
                f"Could not create medicine record: {error}"
            )

            st.stop()

        # ----------------------------------------------------
        # PROCESS FRAMEWORK
        # ----------------------------------------------------

        with st.spinner(
            "Running pharmaceutical verification..."
        ):

            try:

                result = process_medicine(
                    medicine,
                    blockchain=None,
                    save_to_database=True
                )

            except Exception as error:

                st.error(
                    f"Verification failed: {error}"
                )

                st.stop()

        # ----------------------------------------------------
        # RESULT CHECK
        # ----------------------------------------------------

        if not result.get(
            "success",
            False
        ):

            st.error(
                result.get(
                    "error",
                    "Medicine verification failed."
                )
            )

            st.stop()

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        st.success(
            "Medicine verification completed and saved."
        )

        st.divider()

        # ----------------------------------------------------
        # BASIC RESULT
        # ----------------------------------------------------

        st.subheader(
            "📋 Verification Result"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Medicine",
            result["medicine_name"]
        )

        col2.metric(
            "Batch",
            result["batch_number"]
        )

        col3.metric(
            "Risk",
            result["risk_level"]
        )

        col4.metric(
            "Counterfeit",
            result["counterfeit"]
        )

        st.divider()

        # ----------------------------------------------------
        # ATC / MACS / PTI
        # ----------------------------------------------------

        st.subheader(
            "🧠 Trust & Authenticity Scores"
        )

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "ATC Score",
                f"{result['atc']:.2f}"
            )

            st.write(
                f"Status: **{result['atc_status']}**"
            )

        with col2:

            st.metric(
                "MACS Score",
                f"{result['macs']:.2f}"
            )

            st.write(
                f"Status: **{result['macs_status']}**"
            )

        with col3:

            st.metric(
                "PTI Score",
                f"{result['pti']:.2f}"
            )

            st.write(
                f"Status: **{result['pti_status']}**"
            )

        st.divider()

        # ----------------------------------------------------
        # SELF HEALING
        # ----------------------------------------------------

        st.subheader(
            "🔄 Self-Healing Result"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Updated Trust",
            f"{result['updated_trust']:.2f}"
        )

        col2.metric(
            "Updated PTI",
            f"{result['updated_pti']:.2f}"
        )

        col3.metric(
            "Recovery",
            f"{result['recovery']:.2f}"
        )

        col4.metric(
            "Recovery Status",
            result["recovery_status"]
        )

        st.write(
            f"**Network Status:** "
            f"{result['network_status']}"
        )

        # ----------------------------------------------------
        # DETECTED PROBLEMS
        # ----------------------------------------------------

        if result["detected_problems"]:

            st.subheader(
                "⚠️ Detected Problems"
            )

            for problem in result[
                "detected_problems"
            ]:

                st.warning(
                    problem
                )

        else:

            st.success(
                "No verification problems detected."
            )

        # ----------------------------------------------------
        # TECHNICAL DETAILS
        # ----------------------------------------------------

        with st.expander(
            "View Technical Verification Details"
        ):

            technical_data = {

                "Medicine Trust":
                    result["medicine_trust"],

                "Verification Success Rate":
                    result["success_rate"],

                "Medicine Integrity":
                    result["medicine_integrity"],

                "Compliance History":
                    result["compliance_history"],

                "Temperature":
                    result["temperature"],

                "Humidity":
                    result["humidity"],

                "Transport Time":
                    result["transport_time"]
            }

            st.json(
                technical_data
            )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

elif page == "📋 Transaction History":

    st.header(
        "📋 Medicine Transaction History"
    )

    try:

        df = load_transactions()

    except Exception as error:

        st.error(
            f"Database error: {error}"
        )

        st.stop()

    if df.empty:

        st.info(
            "No transactions have been saved yet."
        )

    else:

        st.write(
            f"Total transactions: **{len(df)}**"
        )

        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        col1, col2 = st.columns(2)

        with col1:

            risk_filter = st.selectbox(
                "Risk Level",
                [
                    "ALL",
                    "LOW",
                    "MEDIUM",
                    "HIGH"
                ]
            )

        with col2:

            counterfeit_filter = st.selectbox(
                "Counterfeit Status",
                [
                    "ALL",
                    "NO",
                    "POSSIBLE",
                    "YES"
                ]
            )

        filtered = df.copy()

        if risk_filter != "ALL":

            filtered = filtered[
                filtered["risk_level"]
                == risk_filter
            ]

        if counterfeit_filter != "ALL":

            filtered = filtered[
                filtered["counterfeit"]
                == counterfeit_filter
            ]

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        columns = [

            "medicine_id",
            "medicine_name",
            "batch_number",

            "atc",
            "atc_status",

            "macs",
            "macs_status",

            "pti",
            "pti_status",

            "counterfeit",
            "risk_level",

            "recovery",
            "recovery_status",

            "verification_time"
        ]

        st.dataframe(
            filtered[columns],
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        csv = filtered.to_csv(
            index=False
        )

        st.download_button(
            "⬇️ Download Transaction History",
            csv,
            "pharmaceutical_transactions.csv",
            "text/csv"
        )


# ============================================================
# SEARCH MEDICINE
# ============================================================

elif page == "🔎 Search Medicine":

    st.header(
        "🔎 Search Medicine"
    )

    search = st.text_input(
        "Enter Medicine ID, Medicine Name or Batch Number"
    )

    if search:

        try:

            df = load_transactions()

        except Exception as error:

            st.error(
                f"Database error: {error}"
            )

            st.stop()

        search_lower = search.lower()

        results = df[
            df["medicine_id"]
            .astype(str)
            .str.lower()
            .str.contains(
                search_lower,
                na=False
            )
            |
            df["medicine_name"]
            .astype(str)
            .str.lower()
            .str.contains(
                search_lower,
                na=False
            )
            |
            df["batch_number"]
            .astype(str)
            .str.lower()
            .str.contains(
                search_lower,
                na=False
            )
        ]

        if results.empty:

            st.warning(
                "No matching medicine found."
            )

        else:

            st.success(
                f"{len(results)} matching transaction(s) found."
            )

            for _, row in results.iterrows():

                with st.expander(
                    f"{row['medicine_name']} — "
                    f"{row['batch_number']}"
                ):

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "ATC",
                        f"{row['atc']:.2f}"
                    )

                    col2.metric(
                        "MACS",
                        f"{row['macs']:.2f}"
                    )

                    col3.metric(
                        "PTI",
                        f"{row['pti']:.2f}"
                    )

                    col4.metric(
                        "Recovery",
                        f"{row['recovery']:.2f}"
                    )

                    st.write(
                        f"**Medicine ID:** "
                        f"{row['medicine_id']}"
                    )

                    st.write(
                        f"**Batch:** "
                        f"{row['batch_number']}"
                    )

                    st.write(
                        f"**Risk:** "
                        f"{row['risk_level']}"
                    )

                    st.write(
                        f"**Counterfeit:** "
                        f"{row['counterfeit']}"
                    )

                    st.write(
                        f"**ATC Status:** "
                        f"{row['atc_status']}"
                    )

                    st.write(
                        f"**MACS Status:** "
                        f"{row['macs_status']}"
                    )

                    st.write(
                        f"**PTI Status:** "
                        f"{row['pti_status']}"
                    )

                    st.write(
                        f"**Recovery Status:** "
                        f"{row['recovery_status']}"
                    )

                    st.write(
                        f"**Network:** "
                        f"{row['network_status']}"
                    )

                    if row[
                        "detected_problems"
                    ]:

                        st.warning(
                            "Problems: "
                            + str(
                                row[
                                    "detected_problems"
                                ]
                            )
                        )