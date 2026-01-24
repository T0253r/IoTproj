#!/usr/bin/env python3

import time
import sqlite3
import logging
from datetime import datetime
from scapy.all import ARP, Ether, srp
import os
import sys

LEASE_FILE = "/var/lib/misc/dnsmasq.leases"
DB_PATH = "/var/lib/iot/iot.db"
INTERFACE = "wlan0"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def get_db_connection():
    if not os.path.exists(DB_PATH):
        logging.critical(f"No database at {DB_PATH}. Run init_db.py")
        sys.exit(1)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;") 
    return conn

def get_dhcp_devices():
    devices = {}
    try:
        with open(LEASE_FILE, "r") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 4:
                    devices[parts[2]] = {"mac": parts[1], "name": parts[3]}
    except FileNotFoundError:
        logging.error(f"DHCP Lease file not found at {LEASE_FILE}")
    return devices

def verify_active(ip_list):
    if not ip_list:
        return []

    try:
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_list), 
                     timeout=2, verbose=False, iface=INTERFACE)
        
        return [received.psrc for sent, received in ans]
    except Exception as e:
        logging.error(f"Scan failed: {e}")
        return []

def update_database(dhcp_data, active_ips):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            active_macs = []

            for ip in active_ips:
                device_info = dhcp_data.get(ip)
                if device_info:
                    mac = device_info['mac']
                    name = device_info['name']
                    active_macs.append(mac)
                    
                    logging.info(f"Device Online: {name} ({ip})")
                    
                    cursor.execute('''INSERT INTO devices (mac, ip, hostname, online)
                                VALUES (?, ?, ?, 1)
                                ON CONFLICT(mac) DO UPDATE SET
                                ip=excluded.ip, 
                                hostname=excluded.hostname,
                                online=1''', (mac, ip, name))

            if active_macs:
                placeholders = ','.join(['?'] * len(active_macs))
                query = f"UPDATE devices SET online = 0 WHERE mac NOT IN ({placeholders})"
                cursor.execute(query, active_macs)
            else:
                cursor.execute("UPDATE devices SET online = 0")

    except Exception as e:
        logging.error(f"Database update failed: {e}")


def main():
    logging.info("Starting Connected Device Monitor Service...")
    
    while True:
        try:
            logging.info("Checking for connected devices")
            dhcp_data = get_dhcp_devices()
            if dhcp_data:
                active_ips = verify_active(list(dhcp_data.keys()))
                update_database(dhcp_data, active_ips)

        except Exception as e:
            logging.error(f"Critical Monitor Loop Error: {e}")
        
        time.sleep(60)
        

if __name__ == "__main__":
    main()