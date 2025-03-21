import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from jinja2 import ChoiceLoader, FileSystemLoader

# Load environment variables
load_dotenv()

# Initialize Firebase and Firestore (Only Once)
db = None
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)
        db = firestore.client()  # Initialize Firestore client
        print(" Firebase initialized successfully")
    except Exception as e:
        print(f" Error initializing Firebase: {e}")

#  Initialize Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'  # Store session in files

# Configure multiple template folders
app.jinja_loader = ChoiceLoader([
    FileSystemLoader('templates'),
    FileSystemLoader('admin/templates')
])

#  Import routes after app initialization to avoid circular imports
from routes.auth_routes import auth_blueprint
from routes.landing_ai_routes import landing_ai_blueprint
from admin.routes import admin_blueprint  # Updated import path

#  Register Blueprints (Only Once)
app.register_blueprint(auth_blueprint)
app.register_blueprint(landing_ai_blueprint, url_prefix='/api/landing-ai')
app.register_blueprint(admin_blueprint)

# Make db available to blueprints
app.config['db'] = db

@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/api/health')
def health_check():
    return jsonify({"status": "healthy", "firebase": "connected" if db else "disconnected"})

if __name__ == '__main__':
    app.run(debug=True)
