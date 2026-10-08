import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mes_demo.db"

connection = sqlite3.connect(DB_PATH)
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Stations (
    station_id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'ONLINE'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Carts (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    current_station INTEGER,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (current_station) REFERENCES Stations(station_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS CartScans (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_id TEXT NOT NULL,
    station_id INTEGER,
    scan_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    scan_result TEXT NOT NULL DEFAULT 'SUCCESS',
    FOREIGN KEY (station_id) REFERENCES Stations(station_id)
)
""")

# Demo stations
stations = [
    ("Station 01", "ONLINE"),
    ("Station 02", "ONLINE"),
    ("Station 03", "ONLINE"),
    ("Station 04", "OFFLINE"),
]

cursor.executemany("""
INSERT OR IGNORE INTO Stations (station_name, status)
VALUES (?, ?)
""", stations)

connection.commit()
connection.close()

print(f"Database created successfully: {DB_PATH}")