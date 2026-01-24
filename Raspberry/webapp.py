from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "iot_secret_key"
DB_PATH = "/var/lib/iot/iot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_ip(ip):
    """Looks up the device record in the DB based on current IP address."""
    conn = get_db_connection()
    # We look for the device assigned this IP that is currently flagged as online
    user = conn.execute('SELECT * FROM devices WHERE ip = ? AND online = 1', (ip,)).fetchone()
    conn.close()
    return user

@app.route('/')
def index():
    visitor_ip = request.remote_addr
    # Find the user's database record using their IP
    current_user = get_user_by_ip(visitor_ip)
    
    conn = get_db_connection()
    all_devices = conn.execute('SELECT * FROM devices ORDER BY online DESC').fetchall()
    conn.close()
    
    return render_template('index.html', 
                           devices=all_devices, 
                           current_user=current_user,
                           visitor_ip=visitor_ip)

@app.route('/update_username', methods=['POST'])
def update_username():
    visitor_ip = request.remote_addr
    new_name = request.form.get('username')
    
    # Security: Look up the user by IP again to ensure they own the MAC
    user_record = get_user_by_ip(visitor_ip)
    
    if not user_record:
        return "Access Denied: Your IP is not recognized in the device database.", 403

    # Use the MAC found in our DB lookup to perform the update
    # This prevents users from spoofing other MAC addresses in the form
    target_mac = user_record['mac']
    
    conn = get_db_connection()
    conn.execute('UPDATE devices SET username = ? WHERE mac = ?', (new_name, target_mac))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)