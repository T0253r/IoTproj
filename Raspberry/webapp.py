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
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM devices WHERE ip = ? AND online = 1', (ip,)).fetchone()
    conn.close()
    return user

@app.route('/')
def index():
    visitor_ip = request.remote_addr
    current_user = get_user_by_ip(visitor_ip)
    user_mac = current_user['mac'] if current_user else None

    conn = get_db_connection()
    
    controllers_query = '''
        SELECT 
            c.*, 
            p.temp as user_pref_temp,
            d.username as locked_by_name
        FROM controllers c
        LEFT JOIN preferences p 
            ON c.controller_id = p.fk_controller_id 
            AND p.fk_user_mac = ?
        LEFT JOIN devices d
            ON c.set_by = d.mac
    '''
    all_controllers = conn.execute(controllers_query, (user_mac,)).fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                           controllers=all_controllers,
                           current_user=current_user,
                           visitor_ip=visitor_ip)

@app.route('/update_username', methods=['POST'])
def update_username():
    visitor_ip = request.remote_addr
    new_name = request.form.get('username')
    user_record = get_user_by_ip(visitor_ip)
    
    if not user_record:
        return "Access Denied: Your IP is not recognized.", 403

    conn = get_db_connection()
    conn.execute('UPDATE devices SET username = ? WHERE mac = ?', (new_name, user_record['mac']))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/set_manual_temp', methods=['POST'])
def set_manual_temp():
    visitor_ip = request.remote_addr
    controller_id = request.form.get('controller_id')
    target_temp = request.form.get('target_temp')

    user_record = get_user_by_ip(visitor_ip)
    if not user_record:
        return "Access Denied", 403

    conn = get_db_connection()
    conn.execute('''
        UPDATE controllers 
        SET target_temp = ?, set_by = ?, priority = 2 
        WHERE controller_id = ?
    ''', (target_temp, user_record['mac'], controller_id))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/set_preference', methods=['POST'])
def set_preference():
    visitor_ip = request.remote_addr
    controller_id = request.form.get('controller_id')
    pref_temp = request.form.get('pref_temp')

    user_record = get_user_by_ip(visitor_ip)
    if not user_record:
        return "Access Denied", 403

    conn = get_db_connection()
    conn.execute('''
        INSERT OR REPLACE INTO preferences (temp, fk_user_mac, fk_controller_id)
        VALUES (?, ?, ?)
    ''', (pref_temp, user_record['mac'], controller_id))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/clear_preference', methods=['POST'])
def clear_preference():
    visitor_ip = request.remote_addr
    controller_id = request.form.get('controller_id')

    user_record = get_user_by_ip(visitor_ip)
    if not user_record:
        return "Access denied", 403
    
    conn = get_db_connection()
    conn.execute('''
        DELETE FROM preferences
        where fk_user_mac = ? AND fk_controller_id = ?
    ''', (user_record['mac'], controller_id))

    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete_controller', methods=['POST'])
def delete_controller():
    visitor_ip = request.remote_addr
    controller_id = request.form.get('controller_id')

    user_record = get_user_by_ip(visitor_ip)
    if not user_record:
        return "Access Denied", 403

    conn = get_db_connection()
    conn.execute('DELETE FROM controllers WHERE controller_id = ?', (controller_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)