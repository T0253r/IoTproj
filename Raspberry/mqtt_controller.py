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
        logging.critical("No database at {DB_PATH}. Run init_db.py")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;") 
    return conn


def load_known_controllers():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT controller_id FROM rooms").fetchall()
            for row in rows:
                if row['controller_id']:
                    known_controllers.add(row['controller_id'])
        logging.info(f"Loaded known controllers: {known_controllers}")
    except Exception as e:
        logging.error(f"Error laoding controllers: {e}")

def register_new_room(room_id):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO rooms (name, controller_id) VALUES (?, ?)", 
                (f"Nowy {room_id}", room_id)
            )
            logging.info(f"Registered new device: {room_id}")
            known_controllers.add(room_id)
    except Exception as e:
        logging.error(f"Room registration error: {e}")

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        if payload.startswith("ping"):
            parts = payload.split()
            if len(parts) >= 3: 
                room_id = parts[1]
                current_temp = float(parts[2])
                
                if room_id not in known_controllers:
                    register_new_room(room_id)

                with get_db_connection() as conn:
                    conn.execute("""
                        UPDATE rooms 
                        SET current_temp = ?, last_update = CURRENT_TIMESTAMP 
                        WHERE controller_id = ?
                    """, (current_temp, room_id))
                
    except Exception as e:
        logging.error(f"on_message error: {e}")

def sync_loop(client):
    while True:
        try:
            with get_db_connection() as conn:
                rooms = conn.execute("SELECT controller_id, target_temp FROM rooms").fetchall()
            
            for room in rooms:
                c_id = room['controller_id']
                target = room['target_temp']
                if c_id and target is not None:
                    client.publish(f"{c_id}/listen", str(int(target)))

            client.publish("ping", "keep-alive")
            
        except Exception as e:
            logging.error(f"Sync error: {e}")
            
        time.sleep(2)

def main():
    load_known_controllers()

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_message = on_message
    
    logging.info("Connecting with the borker...")
    try:
        client.connect(BROKER, 1883, 60)
    except Exception as e:
        logging.critical(f"MQTT connection error: {e}")
        sys.exit(1)

    client.subscribe("+/send")
    client.loop_start()
    
    logging.info("MQTT Daemon ready")
    
    sync_loop(client)

if __name__ == "__main__":
    main()