#!/usr/bin/env python3

import sqlite3
import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - INIT_DB - %(message)s')

#DB_PATH = "/var/lib/iot/iot.db"
DB_PATH = "iot.db" # relative path for testing

def main():

    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logging.warning("Old databese deleted (reset)")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (mac TEXT PRIMARY KEY,
                  ip TEXT, hostname TEXT,
                  username TEXT,
                  online INTEGER)''')
    c.execute("UPDATE devices SET online = 0")
    c.execute('''CREATE TABLE IF NOT EXISTS controllers (
                        controller_id INTEGER PRIMARY KEY,
                        name TEXT,
                        target_temp REAL,
                        set_by TEXT,
                        curr_temp REAL,
                        last_seen TIMESTAMP,
                        priority INTEGER,
              
                        FOREIGN KEY (set_by) REFERENCES devices(mac)
                            ON DELETE SET NULL ON UPDATE CASCADE
                      )''')
    c.execute('''CREATE TABLE IF NOT EXISTS preferences (
                        temp REAL,
                        fk_user_mac TEXT,
                        
                        fk_controller_id INTEGER,
                        PRIMARY KEY (fk_user_mac, fk_controller_id),
              
                        FOREIGN KEY (fk_user_mac) REFERENCES devices(mac)
                            ON DELETE CASCADE ON UPDATE CASCADE,
                        FOREIGN KEY (fk_controller_id) REFERENCES controllers(controller_id)
                            ON DELETE CASCADE ON UPDATE CASCADE
                      )''')
    conn.commit()
    conn.close()
    logging.info("Database initialized")

if __name__ == "__main__":
    main()