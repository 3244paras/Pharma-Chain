import sqlite3

DB = "pharma_database.db"

try:
    connection = sqlite3.connect(DB)

    cursor = connection.cursor()

    # Check SQLite integrity
    cursor.execute("PRAGMA integrity_check;")

    result = cursor.fetchone()[0]

    print("=" * 60)
    print("DATABASE INTEGRITY CHECK")
    print("=" * 60)

    print("Result:", result)

    # Check number of records
    cursor.execute(
        "SELECT COUNT(*) FROM medicine_transactions"
    )

    count = cursor.fetchone()[0]

    print("Transactions:", count)

    # Display saved records
    cursor.execute("""
        SELECT
            id,
            medicine_id,
            medicine_name,
            batch_number,
            atc,
            macs,
            pti,
            recovery,
            risk_level
        FROM medicine_transactions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    print("\nSAVED MEDICINES")
    print("-" * 60)

    for row in rows:
        print(
            f"ID={row[0]} | "
            f"Medicine={row[2]} | "
            f"Batch={row[3]} | "
            f"ATC={row[4]} | "
            f"MACS={row[5]} | "
            f"PTI={row[6]} | "
            f"Recovery={row[7]} | "
            f"Risk={row[8]}"
        )

    connection.close()

except Exception as e:

    print("=" * 60)
    print("DATABASE ERROR")
    print("=" * 60)

    print(type(e).__name__)
    print(e)