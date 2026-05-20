import sqlite3
import csv
import datetime
import os

DB_NAME = "scanner_history.db"

def init_db():
    """Initialize the SQLite database and create the scans table if it doesn't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_data TEXT UNIQUE NOT NULL,
            scan_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_scan(scan_data, scan_type):
    """
    Add a new scan to the database.
    Prevents duplicates by relying on the UNIQUE constraint on scan_data.
    Returns True if added successfully, False if it's a duplicate.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO scans (scan_data, scan_type) VALUES (?, ?)",
            (scan_data, scan_type)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate entry
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def get_all_scans():
    """Retrieve all scan history, ordered by newest first."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # To return dict-like rows
    cursor = conn.cursor()
    cursor.execute("SELECT id, scan_data, scan_type, timestamp FROM scans ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def export_to_csv(filepath):
    """Export the current scan history to a CSV file."""
    scans = get_all_scans()
    with open(filepath, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Data', 'Type', 'Timestamp'])
        for scan in scans:
            writer.writerow([scan['id'], scan['scan_data'], scan['scan_type'], scan['timestamp']])

def get_scan_stats_by_type():
    """Get scan counts grouped by type for analytics."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT scan_type, COUNT(*) FROM scans GROUP BY scan_type")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_scan_stats_by_date():
    """Get scan counts grouped by date (YYYY-MM-DD)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT date(timestamp), COUNT(*) FROM scans GROUP BY date(timestamp) ORDER BY date(timestamp)")
    rows = cursor.fetchall()
    conn.close()
    return rows
