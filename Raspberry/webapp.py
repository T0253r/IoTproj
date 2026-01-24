#!/usr/bin/env python3

from flask import Flask, jsonify, request, render_template
import sqlite3
import logging
import os

app = Flask(__name__)
DB_PATH = "/var/lib/iot/iot.db"
#DB_PATH = "iot.db" # relative path for testing

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- SERVE HTML ---

@app.route('/')
def index():
    # Flask automatically looks for "index.html" inside the "templates" folder
    return render_template('index.html')

# --- API ENDPOINTS ---

@app.route('/api/controllers', methods=['GET'])
def get_controllers():
    """Returns list of all HVAC controllers."""
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM controllers ORDER BY name").fetchall()
            return jsonify([dict(row) for row in rows])
    except Exception as e:
        return jsonify([])

@app.route('/api/controllers/<int:controller_id>/target', methods=['POST'])
def set_target_temp(controller_id):
    """Sets the target temperature for a specific controller."""
    data = request.json
    target = data.get('target')
    
    if target is None:
        return jsonify({"error": "Missing target temperature"}), 400
        
    try:
        with get_db() as conn:
            conn.execute(
                "UPDATE controllers SET target_temp = ? WHERE controller_id = ?",
                (target, controller_id)
            )
            conn.commit()
        return jsonify({"status": "success", "target": target})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Returns all detected network devices."""
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM devices ORDER BY online DESC, last_seen DESC").fetchall()
            devices = []
            for row in rows:
                d = dict(row)
                # Helper for JS to select IDs easily (removes colons from MAC)
                d['mac_safe'] = d['mac'].replace(':', '') 
                devices.append(d)
            return jsonify(devices)
    except Exception as e:
        return jsonify([])

@app.route('/api/devices/<path:mac>/name', methods=['POST'])
def set_device_name(mac):
    """Associates a Username with a MAC address."""
    data = request.json
    username = data.get('username')
    
    with get_db() as conn:
        conn.execute(
            "UPDATE devices SET username = ? WHERE mac = ?",
            (username, mac)
        )
        conn.commit()
    return jsonify({"status": "updated", "mac": mac, "username": username})

if __name__ == '__main__':
    # Running on 0.0.0.0 allows access from other devices on the LAN
    app.run(host='0.0.0.0', port=5000, debug=True)