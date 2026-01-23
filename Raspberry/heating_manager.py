#!/usr/bin/env python3

import time
import sqlite3
import paho.mqtt.client as mqtt
import logging
import sys
import os

DB_PATH = "/home/akkm/iot.db"
BROKER = "127.0.0.1"
PORT = 1883

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
            rows = conn.execute("SELECT controller_id FROM rooms").fetchall() # bazodanowe rzeczy do zmiany
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
                "INSERT OR IGNORE INTO rooms (name, controller_id) VALUES (?, ?)", # bazodanowe rzeczy do zmiany
                (f"Nowy {controller_id}", controller_id)
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

        with get_db_connection() as conn: # bazodanowe rzeczy do zmiany
            conn.execute("""
                UPDATE rooms 
                SET current_temp = ?, last_update = CURRENT_TIMESTAMP 
                WHERE controller_id = ?
            """, (current_temp, controller_id))
                
    except Exception as e:
        logging.error(f"on_message error: {e}")

def sync_loop(client):
    while True:
        try:
            with get_db_connection() as conn:
                controllers = conn.execute("SELECT controller_id, target_temp FROM rooms").fetchall()
            
            for controller in controllers:
                c_id = controller['controller_id']
                target = controller['target_temp']
                if c_id and target is not None:
                    client.publish(f"controllers/{c_id}/set-temp", str(int(target)))
            
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

    client.subscribe("controllers/+/read-temp")
    client.loop_start()
    
    logging.info("MQTT Daemon ready")
    
    sync_loop(client)

if __name__ == "__main__":
    main()