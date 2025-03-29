from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, current_app
from firebase_admin import firestore, auth
from datetime import datetime, timedelta
from collections import Counter
import os

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

def get_db():
    """Get the Firestore database instance"""
    return current_app.config['db']

def is_admin_user(email):
    """Check if the user is an admin by checking their email domain or specific list"""
    admin_domains = ['dut.ac.za', 'admin.com']  # Add your admin domains here
    admin_emails = ['admin@example.com']  # Add specific admin emails here
    
    return any(email.endswith(domain) for domain in admin_domains) or email in admin_emails

def get_activity_icon(activity_type):
    """Get the appropriate icon for different activity types"""
    icons = {
        'checkin': 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
        'registration': 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z',
        'profile_update': 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
        'system': 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z'
    }
    return icons.get(activity_type, icons['system'])

def get_activity_color(activity_type):
    """Get the appropriate color for different activity types"""
    colors = {
        'checkin': 'bg-green-100 text-green-800',
        'registration': 'bg-blue-100 text-blue-800',
        'profile_update': 'bg-yellow-100 text-yellow-800',
        'system': 'bg-gray-100 text-gray-800'
    }
    return colors.get(activity_type, colors['system'])

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
        try:
            email = request.form.get("email")
            password = request.form.get("password")

            # Sign in with Firebase
            user = auth.get_user_by_email(email)
            
            # Check if user is an admin
            if not is_admin_user(email):
                return render_template('admin_login.html', error="Unauthorized access. Admin privileges required.")
            
            # Store admin session
            session['admin_logged_in'] = True
            session['admin_email'] = email
            session['admin_uid'] = user.uid
            
            print(f"Admin logged in: {email}")
            return redirect(url_for('admin.admin_dashboard'))
            
        except auth.UserNotFoundError:
            return render_template('admin_login.html', error="User not found")
        except auth.WrongPasswordError:
            return render_template('admin_login.html', error="Incorrect password")
        except Exception as e:
            print(f"Login error: {str(e)}")
            return render_template('admin_login.html', error="An error occurred during login")
    
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
        
        # Get recent activities (check-ins, registrations, profile updates)
        activities = []
        
        # Get check-ins
        checkins_ref = db.collection('checkins').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        for doc in checkins_ref.stream():
            checkin = doc.to_dict()
            checkin['id'] = doc.id
            checkin['type'] = 'checkin'
            activities.append(checkin)
        
        # Get registrations
        users_ref = db.collection('users').order_by('created_at', direction=firestore.Query.DESCENDING).limit(10)
        for doc in users_ref.stream():
            user = doc.to_dict()
            user['id'] = doc.id
            user['type'] = 'registration'
            activities.append(user)
        
        # Get profile updates
        profile_updates = db.collection('profile_updates').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        for doc in profile_updates.stream():
            update = doc.to_dict()
            update['id'] = doc.id
            update['type'] = 'profile_update'
            activities.append(update)
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x.get('timestamp', x.get('created_at', datetime.min)), reverse=True)
        activities = activities[:20]  # Limit to 20 most recent activities

        return render_template('admin_dashboard.html', 
                            activities=activities,
                            today_checkins=stats['today_checkins'],
                            total_users=stats['total_users'],
                            pending_profiles=stats['pending_profiles'],
                            most_used_method=stats['most_used_method'],
                            get_activity_color=get_activity_color,  # Pass the function to template
                            get_activity_icon=get_activity_icon)    # Pass the function to template
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({"error": str(e)}), 500

@admin_blueprint.route('/api/activities')
def get_activities():
    """API endpoint to get recent activities"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        activities = []
        
        # Get check-ins
        checkins_ref = db.collection('checkins').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        for doc in checkins_ref.stream():
            checkin = doc.to_dict()
            checkin['id'] = doc.id
            checkin['type'] = 'checkin'
            # Convert Firestore timestamp to ISO string
            if 'timestamp' in checkin:
                checkin['timestamp'] = checkin['timestamp'].isoformat()
            activities.append(checkin)
        
        # Get registrations
        users_ref = db.collection('users').order_by('created_at', direction=firestore.Query.DESCENDING).limit(10)
        for doc in users_ref.stream():
            user = doc.to_dict()
            user['id'] = doc.id
            user['type'] = 'registration'
            # Convert Firestore timestamp to ISO string
            if 'created_at' in user:
                user['created_at'] = user['created_at'].isoformat()
            activities.append(user)
        
        # Get profile updates
        profile_updates = db.collection('profile_updates').order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        for doc in profile_updates.stream():
            update = doc.to_dict()
            update['id'] = doc.id
            update['type'] = 'profile_update'
            # Convert Firestore timestamp to ISO string
            if 'timestamp' in update:
                update['timestamp'] = update['timestamp'].isoformat()
            activities.append(update)
        
        # Sort all activities by timestamp
        activities.sort(key=lambda x: x.get('timestamp', x.get('created_at', '')), reverse=True)
        activities = activities[:20]  # Limit to 20 most recent activities

        # Return only the activities, helper functions are already available in the template
        return jsonify({"activities": activities})
    except Exception as e:
        print(f"Error fetching activities: {e}")
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
        users = []
        
        for doc in users_ref.stream():
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            
            # Get last check-in for this user
            checkins_ref = db.collection('checkins')
            # Query check-ins for this user's student_id
            checkins = checkins_ref.where('student_id', '==', user_data['student_id']).stream()
            
            # Find the most recent check-in
            last_checkin = None
            for checkin in checkins:
                checkin_data = checkin.to_dict()
                if not last_checkin or (checkin_data.get('timestamp') and 
                    checkin_data['timestamp'] > last_checkin.get('timestamp', datetime.min)):
                    last_checkin = checkin_data
            
            if last_checkin:
                user_data['last_checkin'] = last_checkin.get('timestamp')
            
            users.append(user_data)
        
        # Sort users by last name
        users.sort(key=lambda x: x.get('last_name', ''))
        
        return render_template('admin_users.html', users=users)
    except Exception as e:
        print(f"Error listing users: {e}")
        return render_template('admin_users.html', users=[], error=str(e))

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

        if not user_doc.exists:
            return redirect(url_for('admin.list_users'))

        user = user_doc.to_dict()
        user['id'] = user_doc.id

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

        # Get user's check-ins
        checkins_ref = db.collection('checkins')
        checkins = []
        # Query check-ins for this user's student_id
        checkins_query = checkins_ref.where('student_id', '==', user['student_id']).stream()
        
        # Convert to list and sort by timestamp
        for doc in checkins_query:
            checkin = doc.to_dict()
            checkin['id'] = doc.id
            checkins.append(checkin)
        
        # Sort check-ins by timestamp in descending order
        checkins.sort(key=lambda x: x.get('timestamp', datetime.min), reverse=True)

        return render_template('admin_edit_user.html', user=user, checkins=checkins)
    except Exception as e:
        print(f"Error managing user: {e}")
        return render_template('admin_edit_user.html', user=user, checkins=[], error=str(e))

@admin_blueprint.route('/users/<user_id>/delete', methods=['POST'])
def delete_user(user_id):
    """Delete a user and their associated data"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        
        # First check if user exists
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404
            
        # Delete user document
        user_ref.delete()
        
        # Delete associated check-ins
        checkins_ref = db.collection('checkins')
        checkins = checkins_ref.where('student_id', '==', user_id).stream()
        for checkin in checkins:
            checkin.reference.delete()
            
        # Delete associated profile updates
        profile_updates = db.collection('profile_updates').where('student_id', '==', user_id).stream()
        for update in profile_updates:
            update.reference.delete()

        return jsonify({"message": "User deleted successfully"})
    except Exception as e:
        print(f"Error deleting user: {e}")
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

@admin_blueprint.route('/users/<user_id>/toggle-auth/<method>', methods=['POST'])
def toggle_auth_method(user_id, method):
    """Toggle an authentication method for a user"""
    if not session.get('admin_logged_in'):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        db = get_db()
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()

        if not user_doc.exists:
            return jsonify({"error": "User not found"}), 404

        user_data = user_doc.to_dict()
        auth_methods = user_data.get('auth_methods', [])

        if method in auth_methods:
            # Remove the method
            auth_methods.remove(method)
        else:
            # Add the method
            auth_methods.append(method)

        # Update the user document
        user_ref.update({
            'auth_methods': auth_methods,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

        return jsonify({
            "message": f"Authentication method '{method}' toggled successfully",
            "auth_methods": auth_methods
        })
    except Exception as e:
        print(f"Error toggling auth method: {e}")
        return jsonify({"error": str(e)}), 500
