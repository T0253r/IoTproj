#!/usr/bin/env python3

import sqlite3
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - INIT_DB - %(message)s')

DB_PATH = "/home/akkm/iot.db"

def main():

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logging.warning("Old databese deleted (reset)")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (mac TEXT PRIMARY KEY,
                  ip TEXT, hostname TEXT,
                  last_seen TIMESTAMP,
                  online INTEGER)''')
    c.execute("UPDATE devices SET online = 0")
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        controller_id TEXT,
                        locked_by TEXT
                      )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_rooms (
                        user_mac TEXT NOT NULL,
                        room_id INTEGER NOT NULL,
                        temp REAL NOT NULL,
                        PRIMARY KEY (user_mac, room_id),
                        FOREIGN KEY(user_mac) REFERENCES users(mac) ON DELETE CASCADE,
                        FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE
                      )''')
    conn.commit()
    conn.close()
    logging.info("Database initialized")

if __name__ == "__main__":
    main()