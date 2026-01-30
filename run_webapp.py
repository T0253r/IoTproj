#!/usr/bin/env python3

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_PATH = "iot.db"
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = 5000

def check_requirements():
    """Check if required packages are installed"""
    logging.info("Checking requirements...")
    try:
        import flask
        import flasgger
        logging.info("✓ All required packages are installed")
        return True
    except ImportError as e:
        logging.error(f"✗ Missing required package: {e}")
        logging.error("Please install requirements: pip install -r requirements.txt")
        return False

def init_database():
    """Initialize the database"""
    logging.info("=" * 60)
    logging.info("STEP 1: Initializing database...")
    logging.info("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'Raspberry'))
        
        sys.path.insert(0, os.getcwd())
        import db_init
        
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            logging.info("Removed existing database")
        
        db_init.main()
        logging.info("✓ Database initialized successfully\n")
        
        os.chdir(original_dir)
        return True
    except Exception as e:
        logging.error(f"✗ Failed to initialize database: {e}")
        return False

def create_mock_controllers():
    """Create mock controller data"""
    logging.info("=" * 60)
    logging.info("STEP 2: Creating mock controllers...")
    logging.info("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'Raspberry'))
        
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mock_scripts'))
        import mock_controllers
        
        mock_controllers.create_mock_controllers()
        logging.info("✓ Mock controllers created successfully\n")
        
        os.chdir(original_dir)
        return True
    except Exception as e:
        logging.error(f"✗ Failed to create mock controllers: {e}")
        return False

def create_mock_devices():
    """Create mock device data"""
    logging.info("=" * 60)
    logging.info("STEP 3: Creating mock devices...")
    logging.info("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'Raspberry'))
        
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mock_scripts'))
        import mock_devices
        
        mock_devices.create_mock_devices()
        logging.info("✓ Mock devices created successfully\n")
        
        os.chdir(original_dir)
        return True
    except Exception as e:
        logging.error(f"✗ Failed to create mock devices: {e}")
        return False

def verify_database():
    """Verify database content"""
    logging.info("=" * 60)
    logging.info("VERIFICATION: Checking database content...")
    logging.info("=" * 60)
    
    try:
        import sqlite3
        conn = sqlite3.connect(os.path.join('Raspberry', DB_PATH))
        cursor = conn.cursor()
        
        # Check controllers
        cursor.execute("SELECT COUNT(*) FROM controllers")
        controller_count = cursor.fetchone()[0]
        logging.info(f"Controllers in database: {controller_count}")
        
        cursor.execute("SELECT controller_id, name, target_temp, curr_temp FROM controllers")
        for row in cursor.fetchall():
            logging.info(f"  - Controller {row[0]}: {row[1]} (Target: {row[2]}°C, Current: {row[3]}°C)")
        
        # Check devices
        cursor.execute("SELECT COUNT(*) FROM devices")
        device_count = cursor.fetchone()[0]
        logging.info(f"Devices in database: {device_count}")
        
        cursor.execute("SELECT mac, username, hostname, online FROM devices")
        for row in cursor.fetchall():
            status = "Online" if row[3] else "Offline"
            logging.info(f"  - {row[1]} ({row[2]}): {row[0]} - {status}")
        
        conn.close()
        logging.info("✓ Database verification complete\n")
        return True
    except Exception as e:
        logging.error(f"✗ Failed to verify database: {e}")
        return False

def run_webapp():
    """Run the Flask web application"""
    logging.info("=" * 60)
    logging.info("STEP 4: Starting web application...")
    logging.info("=" * 60)
    
    try:
        original_dir = os.getcwd()
        os.chdir(os.path.join(os.path.dirname(__file__), 'Raspberry'))
        
        # Import Flask app
        sys.path.insert(0, os.getcwd())
        from webapp import app
        
        logging.info(f"Starting Flask server on http://{WEBAPP_HOST}:{WEBAPP_PORT}")
        logging.info(f"API Documentation: http://localhost:{WEBAPP_PORT}/api/docs")
        logging.info("Press Ctrl+C to stop the server")
        logging.info("=" * 60)
        
        # Run the app
        app.run(host=WEBAPP_HOST, port=WEBAPP_PORT, debug=True, use_reloader=False)
        
        os.chdir(original_dir)
    except KeyboardInterrupt:
        logging.info("\n\nShutting down web application...")
    except Exception as e:
        logging.error(f"✗ Failed to run web application: {e}")
        return False


if __name__ == "__main__":
    
    if not check_requirements():
        sys.exit(1)
    
    if not init_database():
        logging.error("Database initialization failed. Exiting.")
        sys.exit(1)
    
    if not create_mock_controllers():
        logging.error("Mock controller creation failed. Exiting.")
        sys.exit(1)
    
    if not create_mock_devices():
        logging.error("Mock device creation failed. Exiting.")
        sys.exit(1)
    
    if not verify_database():
        logging.warning("Database verification failed, but continuing...")
    
    run_webapp()
