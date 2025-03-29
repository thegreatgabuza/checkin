from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from firebase_admin import firestore
from datetime import datetime

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')

db = firestore.client()

def admin_required(f):
    """Decorator to check if admin is logged in"""
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_blueprint.route('/users')
@admin_required
def list_users():
    """List all registered users"""
    try:
        users_ref = db.collection('users')
        users = []
        for doc in users_ref.stream():
            user_data = doc.to_dict()
            user_data['id'] = doc.id
            
            # Get user's check-ins
            checkins = db.collection('checkins').where('student_id', '==', user_data['student_id']).stream()
            user_data['checkin_count'] = sum(1 for _ in checkins)
            
            users.append(user_data)
            
        return render_template('admin_users.html', users=users)
    except Exception as e:
        flash(f"Error loading users: {str(e)}", 'error')
        return redirect(url_for('admin.admin_dashboard'))

@admin_blueprint.route('/user/<user_id>', methods=['GET', 'POST'])
@admin_required
def manage_user(user_id):
    """View and edit user details"""
    try:
        user_ref = db.collection('users').document(user_id)
        
    if request.method == 'POST':
            # Get current user data
            current_user = user_ref.get()
            if not current_user.exists:
                flash("User not found", 'error')
                return redirect(url_for('admin.list_users'))
            
            current_data = current_user.to_dict()
            
            # Update user data
            update_data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'student_id': request.form.get('student_id'),
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Keep existing authentication methods and data
            if 'registration_methods' in current_data:
                update_data['registration_methods'] = current_data['registration_methods']
            if 'rfid_code' in current_data:
                update_data['rfid_code'] = current_data['rfid_code']
            if 'face_data' in current_data:
                update_data['face_data'] = current_data['face_data']
            if 'voice_data' in current_data:
                update_data['voice_data'] = current_data['voice_data']
            
            # Update the user document
            user_ref.update(update_data)
            
            # If student ID changed, update all related check-ins
            if current_data['student_id'] != update_data['student_id']:
                checkins = db.collection('checkins').where('student_id', '==', current_data['student_id']).stream()
                for checkin in checkins:
                    checkin.reference.update({'student_id': update_data['student_id']})
            
            flash("User updated successfully", 'success')
            return redirect(url_for('admin.list_users'))
        
        # GET request - show edit form
        user = user_ref.get()
        if not user.exists:
            flash("User not found", 'error')
            return redirect(url_for('admin.list_users'))
        
        user_data = user.to_dict()
        user_data['id'] = user.id
        
        # Get user's check-ins
        checkins = []
        checkins_ref = db.collection('checkins').where('student_id', '==', user_data['student_id']).order_by('timestamp', direction=firestore.Query.DESCENDING).stream()
        for doc in checkins_ref:
            checkin_data = doc.to_dict()
            checkin_data['id'] = doc.id
            checkins.append(checkin_data)
        
        return render_template('admin_edit_user.html', user=user_data, checkins=checkins)
        
    except Exception as e:
        flash(f"Error managing user: {str(e)}", 'error')
        return redirect(url_for('admin.list_users'))

@admin_blueprint.route('/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete a user and their check-ins"""
    try:
        # Get user data first
        user_ref = db.collection('users').document(user_id)
        user = user_ref.get()
        
        if not user.exists:
            flash("User not found", 'error')
            return redirect(url_for('admin.list_users'))
        
        user_data = user.to_dict()
        
        # Delete all check-ins for this user
        batch = db.batch()
        checkins = db.collection('checkins').where('student_id', '==', user_data['student_id']).stream()
        
        for checkin in checkins:
            batch.delete(checkin.reference)
        
        # Delete the user
        batch.delete(user_ref)
        
        # Commit all deletions in one batch
        batch.commit()
        
        flash("User and associated check-ins deleted successfully", 'success')
        return redirect(url_for('admin.list_users'))
        
    except Exception as e:
        flash(f"Error deleting user: {str(e)}", 'error')
        return redirect(url_for('admin.list_users'))

@admin_blueprint.route('/checkin/<checkin_id>/delete', methods=['POST'])
@admin_required
def delete_checkin(checkin_id):
    """Delete a specific check-in"""
    try:
        checkin_ref = db.collection('checkins').document(checkin_id)
        checkin = checkin_ref.get()
        
        if not checkin.exists:
            flash("Check-in not found", 'error')
            return redirect(request.referrer or url_for('admin.admin_dashboard'))
        
        checkin_ref.delete()
        flash("Check-in deleted successfully", 'success')
        
    except Exception as e:
        flash(f"Error deleting check-in: {str(e)}", 'error')
    
    return redirect(request.referrer or url_for('admin.admin_dashboard'))

@admin_blueprint.route('/user/<user_id>/toggle_auth_method', methods=['POST'])
@admin_required
def toggle_auth_method(user_id):
    """Enable or disable an authentication method for a user"""
    try:
        method = request.form.get('method')
        action = request.form.get('action')  # 'enable' or 'disable'
        
        if not method or not action:
            return jsonify({'error': 'Missing parameters'}), 400
            
        user_ref = db.collection('users').document(user_id)
        user = user_ref.get()
        
        if not user.exists:
            return jsonify({'error': 'User not found'}), 404
            
        user_data = user.to_dict()
        methods = set(user_data.get('registration_methods', []))
        
        if action == 'enable':
            methods.add(method)
        else:
            methods.discard(method)
            # Remove associated data
            if method == 'rfid':
                user_data.pop('rfid_code', None)
            elif method == 'facial':
                user_data.pop('face_data', None)
            elif method == 'voice':
                user_data.pop('voice_data', None)
        
        user_data['registration_methods'] = list(methods)
        user_ref.update(user_data)
        
        return jsonify({'success': True, 'methods': list(methods)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 