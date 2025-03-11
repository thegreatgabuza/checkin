import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load environment variables
load_dotenv()

#  Initialize Flask Application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['SESSION_TYPE'] = 'filesystem'  # Store session in files
app.config['SESSION_PERMANENT'] = False    # Make session temporary

#  Initialize Firebase (Prevent Duplicate Initialization)
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate('firebase-key.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print(" Firebase initialized successfully")
except Exception as e:
    print(f" Error initializing Firebase: {e}")
    db = None

#  Import routes after app initialization to avoid circular imports
from routes.auth_routes import auth_blueprint
from routes.landing_ai_routes import landing_ai_blueprint
from routes.admin_routes import admin_blueprint

#  Register Blueprints (Only Once)
app.register_blueprint(auth_blueprint)
app.register_blueprint(landing_ai_blueprint)
app.register_blueprint(admin_blueprint)

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

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


#  SECURED ADMIN PANEL 


ADMIN_PASSWORD = "securepassword123"  #  Change in production!

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:  #  Correct password
            session['admin_logged_in'] = True  #  Store admin session
            return redirect(url_for('admin_dashboard'))

        return render_template('admin_login.html', error="Incorrect password!")  # 
    
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    """🔒 Secure Admin Dashboard - Only accessible if logged in"""
    if not session.get('admin_logged_in'):  #  Check if admin is logged in
        return redirect(url_for('admin_login'))  # Redirect to login page

    try:
        checkins_ref = db.collection('checkins')
        checkins = [doc.to_dict() for doc in checkins_ref.stream()]
        return render_template('admin_dashboard.html', checkins=checkins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)  #  Remove admin session
    return redirect(url_for('admin_login'))

@app.route('/admin/create_profile/<student_id>', methods=['POST'])
def create_profile(student_id):
    """Allow admin to create a student profile after check-in"""
    if not session.get('admin_logged_in'):  #  Protect profile creation
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = request.json  # Get data from form
        student_ref = db.collection('students').document(student_id)

        # Create the student profile
        student_ref.set({
            "student_id": student_id,
            "name": data.get("name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "registered_at": firestore.SERVER_TIMESTAMP
        })

        # Update check-in record to mark profile as created
        db.collection('checkins').document(student_id).update({
            "profile_created": True
        })

        return jsonify({"message": "Profile created successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
