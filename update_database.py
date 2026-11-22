import sqlite3

DATABASE_NAME = "pharma_database.db"

conn = sqlite3.connect(DATABASE_NAME)
cursor = conn.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(medicine_transactions)")
existing_columns = [row[1] for row in cursor.fetchall()]

# New columns required by the updated application
new_columns = {
    "manufacturer_location": "TEXT",
    "distributor_location": "TEXT",
    "pharmacy_location": "TEXT",
    "latitude": "REAL",
    "longitude": "REAL",
}

for column, data_type in new_columns.items():

    if column not in existing_columns:

        cursor.execute(
            f"ALTER TABLE medicine_transactions "
            f"ADD COLUMN {column} {data_type}"
        )

        print(f"Added column: {column}")

    else:

        print(f"Already exists: {column}")

conn.commit()
conn.close()

print("\nDatabase migration completed successfully.")