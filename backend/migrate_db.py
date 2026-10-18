
import sqlite3

connection = sqlite3.connect("lifeline.db")

columns = [
    row[1]
    for row in connection.execute(
        "PRAGMA table_info(emergency_requests)"
    )
]

if "urgency" not in columns:
    connection.execute(
        "ALTER TABLE emergency_requests "
        "ADD COLUMN urgency VARCHAR NOT NULL DEFAULT 'Normal'"
    )
    print("Urgency column added successfully!")
else:
    print("Urgency column already exists.")

if "request_code" not in columns:
    connection.execute(
        "ALTER TABLE emergency_requests "
        "ADD COLUMN request_code VARCHAR"
    )
    print("Request code column added successfully!")
else:
    print("Request code column already exists.")

connection.commit()
connection.close()

print("Database migration completed!")
