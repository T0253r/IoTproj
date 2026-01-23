#!/usr/bin/env python3

import time
import sqlite3
import paho.mqtt.client as mqtt
import logging
import sys
import os

DB_PATH = "/var/lib/iot/iot.db"
BROKER = "127.0.0.1"
PORT = 1883
MIN_TEMP = 10

logging.basicConfig(level=logging.INFO, format='%(asctime)s - MQTT - %(message)s')

known_controllers = set()

def get_db_connection():
    if not os.path.exists(DB_PATH):
        logging.critical(f"No database at {DB_PATH}. Run init_db.py")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;") 
    return conn


def load_known_controllers():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT controller_id FROM controllers").fetchall()
            for row in rows:
                if row['controller_id']:
                    known_controllers.add(row['controller_id'])
        logging.info(f"Loaded known controllers: {known_controllers}")
    except Exception as e:
        logging.error(f"Error laoding controllers: {e}")

def register_new_controller(controller_id):
    try:
        with get_db_connection() as conn:
            conn.execute( 
                "INSERT OR IGNORE INTO controllers (controller_id, name) VALUES (?, ?)",
                (controller_id, controller_id)
            )
            logging.info(f"Registered new controller: {controller_id}")
            known_controllers.add(controller_id)
    except Exception as e:
        logging.error(f"Controller registration error: {e}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()

        controller_id = topic.split('/')[1]
        current_temp = float(payload)
        
        if controller_id not in known_controllers:
            register_new_controller(controller_id)

        with get_db_connection() as conn:
            conn.execute("""
                UPDATE controllers
                SET current_temp = ?, last_seen = CURRENT_TIMESTAMP 
                WHERE controller_id = ?
            """, (current_temp, controller_id))
                
    except Exception as e:
        logging.error(f"on_message error: {e}")

def process_presence_logic():
    update_sql = '''
    WITH RankedTemps AS (
        SELECT 
            p.fk_controller_id, 
            p.temp,
            devpref.mac as new_user_mac, -- Changed to MAC to match Foreign Key
            ROW_NUMBER() OVER (
                PARTITION BY p.fk_controller_id 
                ORDER BY p.temp DESC
            ) as rank
        FROM preferences p
        JOIN controllers c ON p.fk_controller_id = c.controller_id
        JOIN devices devpref ON p.fk_user_mac = devpref.mac
        LEFT JOIN devices devset ON c.set_by = devset.mac
        WHERE devpref.online = 1
        AND (c.priority < 2 OR c.set_by IS NULL OR devset.online != 1)
    )
    UPDATE controllers
    SET target_temp = rt.temp,
        set_by = rt.new_user_mac,
        priority = 1
    FROM RankedTemps rt
    WHERE controllers.controller_id = rt.fk_controller_id
    AND rt.rank = 1;
    '''
    try:
        with get_db_connection() as conn:
            conn.execute(update_sql)
            conn.commit()
            logging.info(f"Controllers updated based on highest online user preferences. Rows affected: {conn.rowcount}")
    except sqlite3.OperationalError as e:
        logging.error(f"SQL Update failed (likely old SQLite version): {e}")



def sync_loop(client):
    while True:
        try:
            with get_db_connection() as conn:
                controllers = conn.execute("SELECT controller_id, target_temp FROM controllers").fetchall()
            
            for controller in controllers:
                c_id = controller['controller_id']
                target = controller['target_temp']
                if c_id and target is not None:
                    client.publish(f"controllers/{c_id}/target-temp", str(int(target)))
            
        except Exception as e:
            logging.error(f"Sync error: {e}")
            
        time.sleep(5)

def main():
    load_known_controllers()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    logging.info("Connecting with the broker...")
    try:
        client.connect(BROKER, PORT)
    except Exception as e:
        logging.critical(f"MQTT connection error: {e}")
        sys.exit(1)

    client.subscribe("controllers/+/curr-temp")
    client.loop_start()
    
    logging.info("MQTT Daemon ready")
    
    sync_loop(client)

if __name__ == "__main__":
    main()