from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from firebase_admin import firestore
from datetime import datetime, timedelta
from collections import Counter

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

# 🔐 Admin Secret Password (Change this in production)
ADMIN_PASSWORD = "password123"

def get_db():
    """Get the Firestore database instance"""
    return current_app.config['db']

def get_dashboard_stats():
    """Get statistics for the admin dashboard"""
    try:
        db = get_db()
        # Get today's date range
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        # Query check-ins for today
        checkins_ref = db.collection('checkins')
        today_checkins = [
            doc.to_dict() for doc in 
            checkins_ref.where('timestamp', '>=', today)
                        .where('timestamp', '<', tomorrow)
                        .stream()
        ]

        # Get total users
        users_ref = db.collection('users')
        total_users = len([doc.id for doc in users_ref.stream()])

        # Count pending profiles
        pending_profiles = len([
            doc.id for doc in 
            checkins_ref.where('profile_created', '==', False).stream()
        ])

        # Calculate most used method today
        methods = [checkin.get('method', 'unknown') for checkin in today_checkins]
        most_used = Counter(methods).most_common(1)
        most_used_method = most_used[0][0] if most_used else None

        return {
            'today_checkins': len(today_checkins),
            'total_users': total_users,
            'pending_profiles': pending_profiles,
            'most_used_method': most_used_method
        }
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return {
            'today_checkins': 0,
            'total_users': 0,
            'pending_profiles': 0,
            'most_used_method': None
        }

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
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db()
        # Get dashboard statistics
        stats = get_dashboard_stats()
        
        # Get recent check-ins with user data
        checkins_ref = db.collection('checkins').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        checkins = []
        
        for doc in checkins_ref.stream():
            checkin = doc.to_dict()
            # If student_id exists, try to get user data
            if 'student_id' in checkin:
                user_doc = db.collection('users').document(checkin['student_id']).get()
                if user_doc.exists:
                    checkin['user'] = user_doc.to_dict()
            checkins.append(checkin)

        return render_template('admin_dashboard.html', 
                            checkins=checkins,
                            today_checkins=stats['today_checkins'],
                            total_users=stats['total_users'],
                            pending_profiles=stats['pending_profiles'],
                            most_used_method=stats['most_used_method'])
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/users')
def list_users():
    """List all users page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db()
        # Get all users from Firestore
        users_ref = db.collection('users')
        users = [doc.to_dict() for doc in users_ref.stream()]
        
        # Sort users by last name
        users.sort(key=lambda x: x.get('last_name', ''))
        
        return render_template('admin_users.html', users=users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/logout')
def admin_logout():
    """Admin logout"""
    print("🚪 Logging out admin!")  # Debugging
    session.pop('admin_logged_in', None)  # Remove admin session
    return redirect(url_for('admin.admin_login'))

@admin_blueprint.route('/create_profile/<student_id>', methods=['POST'])
def create_profile(student_id):
    """Allow admin to create a student profile after check-in"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
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

@admin_blueprint.route('/verify_profiles')
def verify_profiles():
    """Profile verification page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db()
        # Get pending profiles from check-ins
        checkins_ref = db.collection('checkins')
        pending_profiles = []
        
        for doc in checkins_ref.where('profile_created', '==', False).stream():
            profile = doc.to_dict()
            profile['id'] = doc.id
            pending_profiles.append(profile)
        
        return render_template('verification.html', pending_profiles=pending_profiles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/settings')
def system_settings():
    """System settings page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    try:
        # Get current settings from environment or config
        settings = {
            'landing_ai_key': current_app.config.get('LANDING_AI_KEY', ''),
            'firebase_config': current_app.config.get('FIREBASE_CONFIG', '{}')
        }
        return render_template('settings.html', **settings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/users/<user_id>', methods=['GET', 'POST'])
def manage_user(user_id):
    """Manage individual user page"""
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin.admin_login'))

    try:
        db = get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if request.method == 'POST':
            # Update user data
            user_data = {
                'student_id': request.form.get('student_id'),
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            user_ref.update(user_data)
            return redirect(url_for('admin.list_users'))

        if not user_doc.exists:
            return redirect(url_for('admin.list_users'))

        user = user_doc.to_dict()
        user['id'] = user_doc.id

        # Get user's check-ins
        checkins_ref = db.collection('checkins')
        checkins = [
            doc.to_dict() for doc in 
            checkins_ref.where('student_id', '==', user_id)
                        .order_by('timestamp', direction=firestore.Query.DESCENDING)
                        .limit(10)
                        .stream()
        ]

        return render_template('admin_edit_user.html', user=user, checkins=checkins)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        # Delete user document
        db.collection('users').document(user_id).delete()
        
        # Delete associated check-ins
        checkins_ref = db.collection('checkins')
        checkins = checkins_ref.where('student_id', '==', user_id).stream()
        for checkin in checkins:
            checkin.reference.delete()

        return redirect(url_for('admin.list_users'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/checkins/<checkin_id>/delete', methods=['POST'])
def delete_checkin(checkin_id):
    """Delete a check-in"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        db.collection('checkins').document(checkin_id).delete()
        return redirect(request.referrer or url_for('admin.admin_dashboard'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
