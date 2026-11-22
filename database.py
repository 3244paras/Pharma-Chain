import sqlite3
from datetime import datetime


DATABASE_NAME = "pharma_database.db"


# ==========================================================
# DATABASE CONNECTION
# ==========================================================

def get_connection():
    return sqlite3.connect(DATABASE_NAME)


# ==========================================================
# CREATE DATABASE TABLE
# ==========================================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_transactions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            medicine_id TEXT NOT NULL,
            medicine_name TEXT NOT NULL,
            batch_number TEXT NOT NULL,

            manufacturer TEXT,
            distributor TEXT,
            pharmacy TEXT,

            temperature REAL,
            humidity REAL,
            transport_time REAL,

            qr_verified INTEGER,
            package_intact INTEGER,
            batch_verified INTEGER,

            atc REAL,
            atc_status TEXT,

            macs REAL,
            macs_status TEXT,

            counterfeit TEXT,
            risk_level TEXT,

            pti REAL,
            pti_status TEXT,

            updated_trust REAL,
            updated_pti REAL,

            recovery REAL,
            recovery_status TEXT,

            network_status TEXT,
            detected_problems TEXT,

            verification_time TEXT
        )
    """)

    connection.commit()
    connection.close()


# ==========================================================
# SAVE MEDICINE TRANSACTION
# ==========================================================

def save_transaction(result):

    connection = get_connection()
    cursor = connection.cursor()

    problems = result.get("detected_problems", [])

    if isinstance(problems, list):
        problems = "; ".join(problems)

    cursor.execute("""
        INSERT INTO medicine_transactions (

            medicine_id,
            medicine_name,
            batch_number,

            manufacturer,
            distributor,
            pharmacy,

            temperature,
            humidity,
            transport_time,

            qr_verified,
            package_intact,
            batch_verified,

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
        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        result.get("medicine_id"),
        result.get("medicine_name"),
        result.get("batch_number"),

        result.get("manufacturer", ""),
        result.get("distributor", ""),
        result.get("pharmacy", ""),

        result.get("temperature", 0),
        result.get("humidity", 0),
        result.get("transport_time", 0),

        int(result.get("qr_verified", False)),
        int(result.get("package_intact", False)),
        int(result.get("batch_verified", False)),

        result.get("atc", 0),
        result.get("atc_status", ""),

        result.get("macs", 0),
        result.get("macs_status", ""),

        result.get("counterfeit", ""),
        result.get("risk_level", ""),

        result.get("pti", 0),
        result.get("pti_status", ""),

        result.get("updated_trust", 0),
        result.get("updated_pti", 0),

        result.get("recovery", 0),
        result.get("recovery_status", ""),

        result.get("network_status", ""),
        problems,

        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()


# ==========================================================
# GET ALL TRANSACTIONS
# ==========================================================

def get_all_transactions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM medicine_transactions
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    connection.close()

    return records


# ==========================================================
# SEARCH TRANSACTIONS
# ==========================================================

def search_transactions(search_text):

    connection = get_connection()

    cursor = connection.cursor()

    search_pattern = f"%{search_text}%"

    cursor.execute("""
        SELECT *
        FROM medicine_transactions

        WHERE medicine_id LIKE ?
           OR medicine_name LIKE ?
           OR batch_number LIKE ?

        ORDER BY id DESC
    """, (
        search_pattern,
        search_pattern,
        search_pattern
    ))

    records = cursor.fetchall()

    connection.close()

    return records


# ==========================================================
# GET TRANSACTION COUNT
# ==========================================================

def get_total_transactions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM medicine_transactions
    """)

    count = cursor.fetchone()[0]

    connection.close()

    return count


# ==========================================================
# INITIALIZE DATABASE AUTOMATICALLY
# ==========================================================

initialize_database()