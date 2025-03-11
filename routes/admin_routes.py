from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from firebase_admin import firestore

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

db = firestore.client()

# 🔐 Admin Secret Password (Change this in production)
ADMIN_PASSWORD = "password123"

@admin_blueprint.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:  #  Correct password
            session['admin_logged_in'] = True  #  Store admin session
            print(" Admin logged in!")  # Debugging
            return redirect(url_for('admin.admin_dashboard'))
        
        print(" Incorrect password!")  # Debugging
        return render_template('admin_login.html', error="Incorrect password!")  #  Wrong password
    
    return render_template('admin_login.html')

@admin_blueprint.route('/')
def admin_dashboard():
    """🔒 Secure Admin Dashboard - Only accessible if logged in"""
    print("🔍 Checking session:", session)  # Debugging: Print session info

    if not session.get('admin_logged_in'):  #  Check if admin is logged in
        print(" Not logged in! Redirecting to login.")  # Debugging
        return redirect(url_for('admin.admin_login'))  # Redirect to login page

    try:
        checkins_ref = db.collection('checkins')
        checkins = [doc.to_dict() for doc in checkins_ref.stream()]
        return render_template('admin_dashboard.html', checkins=checkins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/logout')
def admin_logout():
    """Admin logout"""
    print("🚪 Logging out admin!")  # Debugging
    session.pop('admin_logged_in', None)  # Remove admin session
    return redirect(url_for('admin.admin_login'))
