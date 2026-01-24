from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "/var/lib/iot/iot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    # Fetch all devices, prioritizing those currently online
    devices = conn.execute('SELECT * FROM devices ORDER BY online DESC, hostname ASC').fetchall()
    conn.close()
    return render_template('index.html', devices=devices)

@app.route('/update_username', methods=['POST'])
def update_username():
    mac = request.form['mac']
    new_username = request.form['username']
    
    conn = get_db_connection()
    conn.execute('UPDATE devices SET username = ? WHERE mac = ?', (new_username, mac))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Ensure the app has permissions to read/write the DB file
    app.run(host='0.0.0.0', port=5000, debug=True)