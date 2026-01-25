from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from flasgger import Swagger, swag_from

app = Flask(__name__)
app.secret_key = "iot_secret_key"
DB_PATH = "/var/lib/iot/iot.db"

# swagger configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "IoT Home Heating Controller API",
        "description": "API for managing IoT heating controllers and user preferences",
        "version": "1.0.0",
        "contact": {
            "name": "IoT Project",
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http"],
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)



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
    """
    Home page
    ---
    tags:
      - Web Interface
    parameters:
      - name: X-Forwarded-For
        in: header
        type: string
        required: false
        description: Client IP address
    responses:
      200:
        description: Renders the main dashboard page
        schema:
          type: string
          example: HTML page with controllers list
    """
    visitor_ip = request.remote_addr
    current_user = get_user_by_ip(visitor_ip)
    user_mac = current_user['mac'] if current_user else None
    user_username = current_user['username'] if current_user else None

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
                           user_username=user_username)

@app.route('/settings')
def settings():
    visitor_ip = request.remote_addr
    current_user = get_user_by_ip(visitor_ip)

    conn = get_db_connection()
    
    controllers_query = '''
        SELECT controller_id, name
        FROM controllers
    '''
    all_controllers = conn.execute(controllers_query).fetchall()
    
    conn.close()
    
    return render_template('settings.html',
                           current_user=current_user,
                           controllers=all_controllers)

@app.route('/update_username', methods=['POST'])
def update_username():
    """
    Update username for the current device
    ---
    tags:
      - Management
    parameters:
      - name: username
        in: formData
        type: string
        required: true
        description: New username for the device
    responses:
      302:
        description: Redirects to home page after successful update
      403:
        description: Access denied - IP not recognized
        schema:
          type: string
          example: "Access Denied: Your IP is not recognized."
    """
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
    """
    Set manual temperature override for a controller
    ---
    tags:
      - Temperature Control
    parameters:
      - name: controller_id
        in: formData
        type: integer
        required: true
        description: ID of the controller to update
      - name: target_temp
        in: formData
        type: number
        required: true
        description: Target temperature to set
    responses:
      302:
        description: Redirects to home page after setting temperature
      403:
        description: Access denied - user not authenticated
        schema:
          type: string
          example: "Access Denied"
    """
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
    """
    Set temperature preference for a controller
    ---
    tags:
      - Temperature Control
    parameters:
      - name: controller_id
        in: formData
        type: integer
        required: true
        description: ID of the controller to set preference for
      - name: pref_temp
        in: formData
        type: number
        required: true
        description: Preferred temperature to set
    responses:
      302:
        description: Redirects to home page after setting preference
      403:
        description: Access denied - user not authenticated
        schema:
          type: string
          example: "Access Denied"
    """
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
    """
    Clear temperature preference for a controller
    ---
    tags:
      - Temperature Control
    parameters:
      - name: controller_id
        in: formData
        type: integer
        required: true
        description: ID of the controller to clear preference for
    responses:
      302:
        description: Redirects to home page after clearing preference
      403:
        description: Access denied - user not authenticated
        schema:
          type: string
          example: "Access denied"
    """
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
    """
    Delete a controller from the system
    ---
    tags:
      - Management
    parameters:
      - name: controller_id
        in: formData
        type: integer
        required: true
        description: ID of the controller to delete
    responses:
      302:
        description: Redirects to home page after deletion
      403:
        description: Access denied - user not authenticated
        schema:
          type: string
          example: "Access Denied"
    """
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

@app.route('/update_controller_name', methods=['POST'])
def update_controller_name():
    """
    Update the name of a controller
    ---
    tags:
      - Management
    parameters:
      - name: controller_id
        in: formData
        type: integer
        required: true
        description: ID of the controller to rename
      - name: name
        in: formData
        type: string
        required: true
        description: New name for the controller
    responses:
      302:
        description: Redirects to home page after updating name
      403:
        description: Access denied - user not authenticated
        schema:
          type: string
          example: "Access Denied"
      404:
        description: Controller not found
        schema:
          type: string
          example: "Controller not found"
    """
    visitor_ip = request.remote_addr
    controller_id = request.form.get('controller_id')
    new_name = request.form.get('name')

    user_record = get_user_by_ip(visitor_ip)
    if not user_record:
        return "Access Denied", 403

    conn = get_db_connection()
    result = conn.execute('UPDATE controllers SET name = ? WHERE controller_id = ?', 
                          (new_name, controller_id))
    conn.commit()
    
    if result.rowcount == 0:
        conn.close()
        return "Controller not found", 404
    
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)