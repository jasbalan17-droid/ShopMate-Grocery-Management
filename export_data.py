import sqlite3
import csv
from pathlib import Path

# Original SQLite database
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "instance" / "shopmate.db"

# Folder to store exported CSV files
EXPORT_DIR = BASE_DIR / "exports"
EXPORT_DIR.mkdir(exist_ok=True)

if not DB_PATH.exists():
    print("Database file not found!")
    raise SystemExit

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

tables = ["product", "sale", "sale_item"]

for table in tables:

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )

    if cursor.fetchone() is None:
        print(f"Table not found: {table}")
        continue

    cursor.execute(f'SELECT * FROM "{table}"')
    rows = cursor.fetchall()

    columns = [
        description[0]
        for description in cursor.description
    ]

    csv_path = EXPORT_DIR / f"{table}.csv"

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(rows)

    print(f"Exported {len(rows)} records from {table}")

connection.close()

print("\nExport completed successfully!")
print("CSV files are saved inside the exports folder.")
