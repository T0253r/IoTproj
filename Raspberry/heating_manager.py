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
    conn = get_db_connection()
    try:
        with conn:
            rows = conn.execute("SELECT controller_id FROM controllers").fetchall()
            for row in rows:
                if row['controller_id']:
                    known_controllers.add(row['controller_id'])
        logging.info(f"Loaded known controllers: {known_controllers}")
    except Exception as e:
        logging.error(f"Error loading controllers: {e}")
    finally:
        conn.close()

def register_new_controller(controller_id):
    logging.info("Attempting to register new controller")
    conn = get_db_connection()
    try:
        with conn:
            conn.execute( 
                "INSERT OR IGNORE INTO controllers (controller_id, name) VALUES (?, ?)",
                (controller_id, controller_id)
            )
            logging.info(f"Registered new controller: {controller_id}")
            known_controllers.add(controller_id)
    except Exception as e:
        logging.error(f"Controller registration error: {e}")
    finally:
        conn.close()

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()

        controller_id = topic.split('/')[1]
        current_temp = float(payload)

        logging.info(f"Received message (id/current): {controller_id}/{current_temp}")
        
        if controller_id not in known_controllers:
            register_new_controller(controller_id)

        conn = get_db_connection()
        try:
            with conn:
                conn.execute("""
                    UPDATE controllers
                    SET current_temp = ?, last_seen = CURRENT_TIMESTAMP 
                    WHERE controller_id = ?
                """, (current_temp, controller_id))
        finally:
            conn.close()
                
    except Exception as e:
        logging.error(f"on_message error: {e}")

def process_presence_logic():
    conn = get_db_connection()
    try:
        with conn:

            # clear set temperatures from users no longer online
            conn.execute('''
                UPDATE controllers
                SET target_temp = ?, 
                    set_by = NULL, 
                    priority = 0
                WHERE set_by IN (SELECT mac FROM devices WHERE online != 1)
            ''', (MIN_TEMP,))

            # set automatic temps where no manual ones are defined
            conn.execute('''
                UPDATE controllers
                SET target_temp = temp_updates.temp,
                    set_by = temp_updates.mac,
                    priority = 1
                FROM (
                    SELECT 
                        p.fk_controller_id, 
                        p.temp, 
                        dev.mac,
                        ROW_NUMBER() OVER (
                            PARTITION BY p.fk_controller_id 
                            ORDER BY p.temp DESC, dev.mac ASC
                        ) as rank_id
                    FROM preferences p
                    JOIN devices dev ON p.fk_user_mac = dev.mac
                    WHERE dev.online = 1
                ) AS temp_updates
                WHERE controllers.controller_id = temp_updates.fk_controller_id
                AND temp_updates.rank_id = 1
                AND (controllers.set_by IS NULL OR controllers.priority < 2);
            ''')

    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()


def sync_loop(client):
    while True:
        try:
            process_presence_logic()

            conn = get_db_connection()
            try:
                with conn:
                    controllers = conn.execute("SELECT controller_id, target_temp FROM controllers").fetchall()
                
                for controller in controllers:
                    c_id = controller['controller_id']
                    target = controller['target_temp']
                    if c_id and target is not None:
                        client.publish(f"controllers/{c_id}/target-temp", str(int(target)))
                        logging.info(f"Published message (id/target): {c_id}/{str(int(target))}")
            finally:
                conn.close()
            
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