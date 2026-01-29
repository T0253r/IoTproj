#!/usr/bin/env python3

import sqlite3
import logging
import sys
import os

# Ensure this matches your project configuration
DB_PATH = "/var/lib/iot/iot.db"
# DB_PATH = "iot.db" # Uncomment for local testing if needed

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MOCK - %(message)s')

def get_db_connection():
    if not os.path.exists(DB_PATH):
        logging.critical(f"Database not found at {DB_PATH}. Please run init_db.py first.")
        sys.exit(1)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_mock_controllers():
    """
    Inserts 3 mock controllers into the database.
    Uses INSERT OR IGNORE so it won't crash if they already exist.
    """
    
    # List of mock data
    mock_data = [
        (1, "Living Room Thermostat", 21.0, 20.5),
        (2, "Bedroom Radiator", 18.0, 19.0),
        (3, "Kitchen Panel", 22.0, 22.1)
    ]

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        logging.info(f"Connecting to database at {DB_PATH}...")

        for c_id, name, target, curr in mock_data:
            cursor.execute('''
                INSERT OR IGNORE INTO controllers 
                (controller_id, name, target_temp, curr_temp, priority, last_seen)
                VALUES (?, ?, ?, ?, 0, datetime('now', '+1 year'))
            ''', (c_id, name, target, curr))
            
            # Optional: If it exists but we want to reset names/values, use UPDATE
            if cursor.rowcount == 0:
                logging.info(f"Controller {c_id} already exists. Skipping insert.")
            else:
                logging.info(f"Created Controller {c_id}: {name}")

        conn.commit()
        conn.close()
        logging.info("Mock controller creation complete.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    create_mock_controllers()