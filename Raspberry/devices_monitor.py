#!/usr/bin/env python3

import time
import sqlite3
import logging
from datetime import datetime
from scapy.all import ARP, Ether, srp
import os

LEASE_FILE = "/var/lib/misc/dnsmasq.leases"
DB_PATH = "/home/akkm/iot.db"
INTERFACE = "wlan0"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

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
    
    ips_to_scan = " ".join(ip_list)
    try:
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ips_to_scan), 
                     timeout=2, verbose=False, iface=INTERFACE)
        return [received.psrc for sent, received in ans]
    except Exception as e:
        logging.error(f"Scan failed: {e}")
        return []

def update_database(conn, dhcp_data, active_ips):
    c = conn.cursor()
    c.execute("UPDATE devices SET online = 0")
    
    for ip in active_ips:
        device_info = dhcp_data.get(ip)
        if device_info:
            logging.info(f"Device Online: {device_info['name']} ({ip})")
            c.execute('''INSERT INTO devices (mac, ip, hostname, last_seen, online)
                         VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                         ON CONFLICT(mac) DO UPDATE SET
                         ip=excluded.ip, 
                         hostname=excluded.hostname,
                         last_seen=excluded.last_seen,
                         online=1''', (device_info['mac'], ip, device_info['name']))
    conn.commit()

def main():
    logging.info("Starting Connected Device Monitor Service...")
    conn = sqlite3.connect(DB_PATH)
    
    while True:
        logging.info("Checking for connected devices")
        dhcp_data = get_dhcp_devices()
        if dhcp_data:
            active_ips = verify_active(list(dhcp_data.keys()))
            update_database(conn, dhcp_data, active_ips)
        
        time.sleep(60)

if __name__ == "__main__":
    main()