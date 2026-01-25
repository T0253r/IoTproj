#!/usr/bin/env python3

import time
import sqlite3
import logging
import os
import sys
from scapy.all import ARP, Ether, srp

LEASE_FILE = "/var/lib/misc/dnsmasq.leases"
DB_PATH = "/var/lib/iot/iot.db"
INTERFACE = "wlan0"
OFFLINE_THRESHOLD = 3
SCAN_INTERVAL = 10

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

def sync_dhcp_to_db():
    try:
        leases = []
        if os.path.exists(LEASE_FILE):
            with open(LEASE_FILE, "r") as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4:
                        leases.append((parts[1], parts[2], parts[3]))
        
        if not leases:
            return

        conn = get_db_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.executemany('''
                    INSERT INTO devices (mac, ip, hostname) VALUES (?, ?, ?)
                    ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    hostname=excluded.hostname
                ''', leases)
        finally:
            conn.close()
    except Exception as e:
        logging.error(f"Error syncing DHCP: {e}")

def get_monitored_devices():
    devices = {}
    conn = get_db_connection()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("SELECT mac, ip, hostname, online FROM devices")
            for row in cursor.fetchall():
                devices[row['mac']] = {
                    'ip': row['ip'],
                    'hostname': row['hostname'],
                    'db_online': bool(row['online'])
                }
    except Exception as e:
        logging.error(f"Error reading DB: {e}")
    finally:
        conn.close()
    return devices

def scan_network(ip_list):
    if not ip_list:
        return set()
    try:
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_list), 
                     timeout=2, verbose=False, iface=INTERFACE)
        return {received.psrc for sent, received in ans}
    except Exception as e:
        logging.error(f"Scanner failed: {e}")
        return set()

def update_db_status(status_updates):
    if not status_updates:
        return
    conn = get_db_connection()
    try:
        with conn:
            conn.executemany("UPDATE devices SET online = ? WHERE mac = ?", status_updates)
    except Exception as e:
        logging.error(f"Error updating DB status: {e}")
    finally:
        conn.close()

def main():
    logging.info("Starting Device Monitor Service...")
    
    missed_scans_counter = {}

    while True:
        sync_dhcp_to_db()
        monitored_devices = get_monitored_devices()
        
        target_ips = [d['ip'] for d in monitored_devices.values() if d['ip']]
        active_ips = scan_network(target_ips)

        db_updates = []
        
        for mac, info in monitored_devices.items():
            ip = info['ip']
            hostname = info['hostname']
            currently_online_in_db = info['db_online']

            if mac not in missed_scans_counter:
                missed_scans_counter[mac] = 0 if currently_online_in_db else OFFLINE_THRESHOLD

            if ip in active_ips:
                if missed_scans_counter[mac] > 0:
                    logging.info(f"Device Reconnected: {hostname} ({ip})")
                
                missed_scans_counter[mac] = 0
                
                if not currently_online_in_db:
                    db_updates.append((1, mac))

            else:
                if missed_scans_counter[mac] < OFFLINE_THRESHOLD:
                    missed_scans_counter[mac] += 1
                    logging.debug(f"{hostname} missed scan {missed_scans_counter[mac]}/{OFFLINE_THRESHOLD}")
                
                if missed_scans_counter[mac] >= OFFLINE_THRESHOLD:
                    if currently_online_in_db:
                        logging.info(f"Device Offline: {hostname} ({ip})")
                        db_updates.append((0, mac))

        update_db_status(db_updates)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()