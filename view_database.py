import sqlite3
import pandas as pd

DATABASE_NAME = "pharma_database.db"


connection = sqlite3.connect(DATABASE_NAME)

query = """
SELECT
    id,
    medicine_id,
    medicine_name,
    batch_number,
    manufacturer,
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

df = pd.read_sql_query(
    query,
    connection
)

connection.close()


print("\n" + "=" * 100)
print("              PHARMACEUTICAL DATABASE")
print("=" * 100)

if df.empty:

    print("\nNo medicine transactions found.")

else:

    print(
        f"\nTotal saved medicines: {len(df)}\n"
    )

    print(df.to_string(index=False))

print("\n" + "=" * 100)