from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from firebase_admin import firestore
from datetime import datetime

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

db = firestore.client()

# 🔐 Admin Secret Password (Change this in production)
ADMIN_PASSWORD = "password123"

def admin_required(f):
    """Decorator to check if admin is logged in"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_blueprint.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        password = request.form.get("password")

        if password == ADMIN_PASSWORD:  #  Correct password
            session['admin_logged_in'] = True  # 🔒 Store admin session
            return redirect(url_for('admin.admin_dashboard'))
        
        return render_template('admin_login.html', error="Incorrect password!")
    
    return render_template('admin_login.html')

@admin_blueprint.route('/')
@admin_required
def admin_dashboard():
    """🔒 Secure Admin Dashboard - Only accessible if logged in"""
    try:
        # Get all check-ins with user data
        checkins_ref = db.collection('checkins')
        checkins = []
        
        for doc in checkins_ref.stream():
            checkin_data = doc.to_dict()
            checkin_data['id'] = doc.id
            
            # Get user data if available
            if 'student_id' in checkin_data:
                user_docs = db.collection('users').where('student_id', '==', checkin_data['student_id']).limit(1).stream()
                user_data = next((doc.to_dict() for doc in user_docs), None)
                if user_data:
                    checkin_data['user'] = user_data
            
            checkins.append(checkin_data)
            
        return render_template('admin_dashboard.html', checkins=checkins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/users')
@admin_required
def list_users():
    """List all registered users"""
    try:
        users_ref = db.collection('users')
        users = [{"id": doc.id, **doc.to_dict()} for doc in users_ref.stream()]
        return render_template('admin_users.html', users=users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/user/<user_id>', methods=['GET', 'POST'])
@admin_required
def manage_user(user_id):
    """View and edit user details"""
    if request.method == 'POST':
        try:
            user_data = request.form.to_dict()
            # Update user data
            db.collection('users').document(user_id).update({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return redirect(url_for('admin.list_users'))
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    try:
        user = db.collection('users').document(user_id).get()
        if user.exists:
            return render_template('admin_edit_user.html', user={"id": user.id, **user.to_dict()})
        return redirect(url_for('admin.list_users'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user and their check-ins"""
    try:
        # Get user data first
        user = db.collection('users').document(user_id).get()
        if not user.exists:
            return jsonify({"error": "User not found"}), 404
        
        user_data = user.to_dict()
        
        # Delete all check-ins for this user
        checkins = db.collection('checkins').where('student_id', '==', user_data['student_id']).stream()
        for checkin in checkins:
            checkin.reference.delete()
            
        # Delete the user
        db.collection('users').document(user_id).delete()
        
        return redirect(url_for('admin.list_users'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/checkin/<checkin_id>/delete', methods=['POST'])
@admin_required
def delete_checkin(checkin_id):
    """Delete a specific check-in"""
    try:
        db.collection('checkins').document(checkin_id).delete()
        return redirect(url_for('admin.admin_dashboard'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)  # 🔓 Remove admin session
    return redirect(url_for('admin.admin_login'))
