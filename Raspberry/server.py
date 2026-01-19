from flask import Flask, render_template, request, redirect, url_for, flash, g
import sqlite3
import threading 
import time
import os
import mqttTempControl as mqttTemp
import connectedDevicesMonitor as devicesMonitor

app = Flask(__name__)
app.secret_key = 'tajny_klucz'
#DB_PATH = "/home/akkm/Documents/connectedDevicesMonitor/roomTemp.db" # czy nie wolimy względnej ścieżki i żeby baza była w plikach projektu?
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "roomTempDb.db")

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        if not os.path.exists(DB_PATH): return None
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS devices
                 (mac TEXT PRIMARY KEY,
                  ip TEXT, hostname TEXT,
                  last_seen TIMESTAMP,
                  online INTEGER)''')
    c.execute("UPDATE devices SET online = 0")
    c.execute('''CREATE TABLE IF NOT EXISTS rooms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        controller_id TEXT,
                        locked_by TEXT
                      )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_rooms (
                        user_mac TEXT NOT NULL,
                        room_id INTEGER NOT NULL,
                        temp REAL NOT NULL,
                        PRIMARY KEY (user_mac, room_id),
                        FOREIGN KEY(user_mac) REFERENCES users(mac) ON DELETE CASCADE,
                        FOREIGN KEY(room_id) REFERENCES rooms(id) ON DELETE CASCADE
                      )''')
    conn.commit()
    return conn

def get_current_user_mac():
    ip = request.remote_addr
    db = get_db()
    if not db: return None
    cur = db.cursor()
    cur.execute("SELECT mac FROM devices WHERE ip = ?", (ip,))
    row = cur.fetchone()
    return row['mac'] if row else None

def release_stale_locks(room_id):
    """
    Checks if the user locking the room is still online.
    If offline, release the lock.
    """
    db = get_db()
    cur = db.cursor()
    
    # Get current lock holder
    cur.execute("SELECT locked_by FROM rooms WHERE id = ?", (room_id,))
    row = cur.fetchone()
    
    if row and row['locked_by']:
        locker_mac = row['locked_by']
        cur.execute("SELECT online FROM devices WHERE mac = ?", (locker_mac,))
        device_status = cur.fetchone()
        
        if not device_status or device_status['online'] == 0:
            cur.execute("UPDATE rooms SET locked_by = NULL WHERE id = ?", (room_id,))
            db.commit()
            return True
    return False

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None: db.close()


"""def background_monitor():
    while True:
        with app.app_context():
            db = get_db()
            if db:
                try:
                    cur = db.cursor()
                    cur.execute("SELECT id FROM rooms")
                    rooms = cur.fetchall()
                    
                    for room in rooms:
                        r_id = str(room['id'])
                        
                        # 1. Używamy metody subscribe z Twojego modułu
                        mqttTemp.subscribe(mqttTemp.LISTEN(r_id))
                        
                        # 2. Wysyłamy ping ręcznie używając klienta z Twojego modułu
                        # (Możesz też dodać metodę 'ping(id)' do mqtt_controller, żeby było czyściej)
                        topic = mqttTemp.SEND(r_id)
                        mqttTemp.client.publish(topic, "ping")
                        
                except Exception as e:
                    print(f"Monitor error: {e}")
        
        time.sleep(2) # Ping co 2 sekundy"""

# --- START APLIKACJI ---
# Uruchamiamy mqttTemp i wątek monitorujący przed startem serwera

#threading.Thread(target=background_monitor, daemon=True).start() - tempControl will take care of this


# --- WIDOKI ---
@app.route('/')
def dashboard():
    return redirect(url_for('room_list')) # Redirect to list view

@app.route('/rooms')
def room_list():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM rooms")
    rooms_db = cur.fetchall()
    
    # Process MQTT data for display
    rooms_display = []
    for room in rooms_db:
        r_dict = dict(room)
        r_id = str(room['id'])
        if r_id in mqttTemp.current_temp:
            data = mqttTemp.current_temp[r_id]
            # Handle tuple or dict depending on your MQTT implementation
            if isinstance(data, (tuple, list)) and len(data) >= 1:
                 r_dict['current_temp'] = data[0]
            elif isinstance(data, dict):
                 r_dict['current_temp'] = data.get('temp', '?')
            else:
                 r_dict['current_temp'] = data
        else:
            r_dict['current_temp'] = "?"
        rooms_display.append(r_dict)
        
    return render_template('dashboard.html', rooms=rooms_display)

@app.route('/room/<int:room_id>')
def room_detail(room_id):
    current_mac = get_current_user_mac()
    if not current_mac:
        flash("Urządzenie nieznane. Połącz się z WiFi.", "error")
        return redirect(url_for('room_list'))

    # 1. Clean up locks before showing data
    release_stale_locks(room_id)

    db = get_db()
    
    # 2. Get Room Data
    room = db.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
    if not room: return "Room not found", 404

    # 3. Get Locker Info (if any)
    locker_name = "Nikt"
    is_locked = False
    can_control = True
    
    if room['locked_by']:
        if room['locked_by'] != current_mac:
            is_locked = True
            can_control = False
            locker = db.execute("SELECT display_name FROM users WHERE mac = ?", (room['locked_by'],)).fetchone()
            locker_name = locker['display_name'] if locker else "Nieznany użytkownik"
        else:
            locker_name = "Ty"

    # 4. Get Current Temp from MQTT
    mqtt_data = mqttTemp.current_temp.get(str(room_id))
    current_temp = mqtt_data[0] if isinstance(mqtt_data, tuple) else (mqtt_data.get('temp') if isinstance(mqtt_data, dict) else "?")

    # 5. Get User's Preferred Temp (from DB history)
    user_pref = db.execute("SELECT preferred_temp FROM user_rooms WHERE user_mac = ? AND room_id = ?", 
                           (current_mac, room_id)).fetchone()
    preferred_temp = user_pref['preferred_temp'] if user_pref else 21.0

    return render_template('room_detail.html', 
                           room=room, 
                           current_temp=current_temp, 
                           locker_name=locker_name, 
                           is_locked=is_locked,
                           can_control=can_control,
                           preferred_temp=preferred_temp)

@app.route('/set_temp/<int:room_id>', methods=['POST'])
def set_temp(room_id):
    current_mac = get_current_user_mac()
    if not current_mac: return redirect(url_for('room_list'))

    target = request.form['target_temp']
    
    db = get_db()
    
    # 1. Save this user's preference regardless of lock
    db.execute('''INSERT INTO user_rooms (user_mac, room_id, preferred_temp) 
                  VALUES (?, ?, ?) 
                  ON CONFLICT(user_mac, room_id) 
                  DO UPDATE SET preferred_temp=excluded.preferred_temp''',
               (current_mac, room_id, target))
    db.commit()

    # 2. Check Lock Status
    room = db.execute("SELECT locked_by FROM rooms WHERE id = ?", (room_id,)).fetchone()
    
    # Check if locked by someone else who is currently ONLINE
    locked_by_other = False
    if room['locked_by'] and room['locked_by'] != current_mac:
        # Check if that user is actually online
        locker_status = db.execute("SELECT online FROM devices WHERE mac = ?", (room['locked_by'],)).fetchone()
        if locker_status and locker_status['online'] == 1:
            locked_by_other = True

    if locked_by_other:
        # LOGIC: Lock exists, do not update controller, just save preference
        flash(f"Zapisano preferencję {target}°C. Zostanie ustawiona, gdy obecny użytkownik się rozłączy.", "info")
    else:
        # LOGIC: Room is free OR locked by me OR locked by offline user -> Take control
        
        # Lock the room to me
        db.execute("UPDATE rooms SET locked_by = ?, target_temp = ? WHERE id = ?", (current_mac, target, room_id))
        db.commit()
        
        # Send to Arduino
        success = mqttTemp.send_to(room_id, target)
        if success:
            flash(f"Temperatura {target}°C ustawiona.", "success")
        else:
            flash("Błąd komunikacji z kontrolerem.", "error")

    return redirect(url_for('room_detail', room_id=room_id))

@app.route('/room/add', methods=['POST'])
def add_room():
    name = request.form['name']
    controller = request.form['controller']
    db = get_db()
    db.execute("INSERT INTO rooms (name, controller_id) VALUES (?, ?)", (name, controller))
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/room/delete/<int:room_id>')
def delete_room(room_id):
    db = get_db()
    db.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
    #db.execute("DELETE FROM room_preferences WHERE room_id = ?", (room_id,)) #on delete cascade should replace this
    db.commit()
    return redirect(url_for('dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user_mac = get_current_user_mac()
    if not user_mac:
        return "Nie rozpoznano urządzenia. Połącz się przez WiFi.", 403
        
    db = get_db()
    
    if request.method == 'POST':
        # Zapisz nazwę profilu
        name = request.form.get('display_name')
        db.execute("INSERT INTO users (mac, name) VALUES (?, ?) ON CONFLICT(mac) DO UPDATE SET name=excluded.name", (user_mac, name))
        
        # Zapisz preferencje dla każdego pokoju
        rooms = db.execute("SELECT id FROM rooms").fetchall()
        for room in rooms:
            pref_temp = request.form.get(f"pref_temp_{room['id']}")
            if pref_temp:
                db.execute('''INSERT INTO room_preferences (user_mac, room_id, preferred_temp) 
                              VALUES (?, ?, ?) 
                              ON CONFLICT(user_mac, room_id) 
                              DO UPDATE SET preferred_temp=excluded.preferred_temp''',
                           (user_mac, room['id'], pref_temp))
        db.commit()
        flash("Zapisano profil", "success")
        return redirect(url_for('dashboard'))

    # GET - Wyświetl formularz
    user = db.execute("SELECT display_name FROM users WHERE mac = ?", (user_mac,)).fetchone()
    rooms = db.execute("SELECT r.id, r.name, p.preferred_temp FROM rooms r LEFT JOIN room_preferences p ON r.id = p.room_id AND p.user_mac = ?", (user_mac,)).fetchall()
    
    return render_template('profile.html', user=user, rooms=rooms, mac=user_mac)

if __name__ == '__main__':
    init_db()
    #mqttTemp.start()
    #devicesMonitor.main()
    app.run(host='0.0.0.0', port=5000, debug=True)