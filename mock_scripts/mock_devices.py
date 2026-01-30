#!/usr/bin/env python3

import sqlite3
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MOCK - %(message)s')

# Auto-detect production vs testing environment
PRODUCTION_DB_PATH = "/opt/iot/db/iot.db"
LOCAL_DB_PATH = "iot.db"
DB_PATH = PRODUCTION_DB_PATH if os.path.exists(os.path.dirname(PRODUCTION_DB_PATH) or "") else LOCAL_DB_PATH

def get_db_connection():
    if not os.path.exists(DB_PATH):
        logging.critical(f"Database not found at {DB_PATH}. Please run init_db.py first.")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_mock_devices():
    """
    Inserts 4 mock devices into the database.
    Uses INSERT OR IGNORE so it won't crash if they already exist.
    """
    
    # List of mock data (mac, ip, hostname, username, online)
    mock_data = [
        ("AA:BB:CC:DD:EE:01", "127.0.0.1", "smartphone-alice", "Alice", 1),
        ("AA:BB:CC:DD:EE:02", "192.168.1.102", "laptop-bob", "Bob", 1),
        ("AA:BB:CC:DD:EE:03", "192.168.1.103", "tablet-charlie", "Charlie", 0),
        ("AA:BB:CC:DD:EE:04", "192.168.1.104", "phone-diana", "Diana", 1)
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logging.info(f"Connecting to database at {DB_PATH}...")

        for mac, ip, hostname, username, online in mock_data:
            cursor.execute('''
                INSERT OR IGNORE INTO devices 
                (mac, ip, hostname, username, online)
                VALUES (?, ?, ?, ?, ?)
            ''', (mac, ip, hostname, username, online))
            
            # Optional: If it exists but we want to reset values, use UPDATE
            if cursor.rowcount == 0:
                logging.info(f"Device {mac} already exists. Skipping insert.")
            else:
                logging.info(f"Created Device: {username} ({hostname}) - MAC: {mac}")

        conn.commit()
        conn.close()
        logging.info("Mock device creation complete.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    create_mock_devices()
