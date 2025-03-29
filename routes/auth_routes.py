from flask import Blueprint, render_template, request, jsonify, redirect, url_for, current_app
import firebase_admin
from firebase_admin import firestore
import json
import os
from datetime import datetime

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')

def get_db():
    """Get the Firestore database instance"""
    return current_app.config['db']

@auth_blueprint.route('/register_manual', methods=['GET', 'POST'])
def register_manual():
    if request.method == 'POST':
        try:
            db = get_db()
            data = request.form
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email', 'student_id', 'date_of_birth']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({"success": False, "error": f"Missing required field: {field}"}), 400
            
            # Check if student ID already exists
            student_id = data.get('student_id')
            existing_user = db.collection('users').where('student_id', '==', student_id).limit(1).get()
            if existing_user:
                return jsonify({"success": False, "error": "Student ID already registered"}), 400
            
            # Create user document
            user_data = {
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'student_id': student_id,
                'date_of_birth': data.get('date_of_birth'),
                'registration_methods': ['manual'],
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add to users collection
            user_ref = db.collection('users').document()
            user_ref.set(user_data)
            
            # Create a check-in record for the user
            check_in_data = {
                'user_id': user_ref.id,
                'student_id': student_id,
                'check_in_time': firestore.SERVER_TIMESTAMP,
                'method': 'manual',
                'status': 'success'
            }
            
            db.collection('check_ins').add(check_in_data)
            
            return jsonify({
                "success": True,
                "message": "Registration successful",
                "user_id": user_ref.id
            })
            
        except Exception as e:
            print(f"Registration error: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
            
    return render_template('register_manual.html')

@auth_blueprint.route('/check_student_id', methods=['POST'])
def check_student_id():
    try:
        data = request.json
        student_id = data.get('student_id')

        if not student_id or not student_id.startswith('2') or len(student_id) != 8:
            return jsonify({"status": "error", "message": "Invalid Student ID"})

        # Check if student already exists in Firestore
        user_ref = get_db().collection('users').document(student_id).get()
        if user_ref.exists:
            return jsonify({"status": "exists", "message": "Student already registered"})

        return jsonify({"status": "not_found", "message": "Student ID not found, proceed with registration."})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@auth_blueprint.route('/register_barcode', methods=['GET', 'POST'])
def register_barcode():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            student_id = data.get('student_id')

            if not student_id or not student_id.startswith('2') or len(student_id) != 8:
                return jsonify({"status": "error", "message": "Invalid Student ID"})

            # Check if student already exists
            user_ref = get_db().collection('users').document(student_id).get()
            if user_ref.exists:
                return jsonify({"status": "exists", "message": "Student already registered"})

            # If student does not exist, ask for additional info
            first_name = data.get('first_name')
            last_name = data.get('last_name')

            if not first_name or not last_name:
                return jsonify({"status": "need_more_info", "message": "Please provide first name and last name."})

            # Save new student to Firestore
            user_ref = get_db().collection('users').document(student_id)
            user_ref.set({
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{student_id}@dut4life.ac.za",
                'student_id': student_id,
                'registration_methods': ['barcode'],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            print(f"Saving student {student_id} to Firestore")
            return jsonify({"status": "success", "message": "User registered successfully"})
        
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})

    return render_template('register_barcode.html')

@auth_blueprint.route('/register_face', methods=['GET', 'POST'])
def register_face():
    if request.method == 'POST':
        try:
            db = get_db()
            data = request.form
            face_data = request.files.get('face_image')
            
            if not face_data:
                return jsonify({"error": "No face image provided"}), 400
                
            # TODO: Process face image with LandingAI
            # For now, just store user data
            user_ref = db.collection('users').document()
            user_ref.set({
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'student_id': data.get('student_id'),
                'registration_methods': ['facial'],
                'face_data': 'placeholder',  # Replace with actual face encoding
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return jsonify({"success": True, "message": "Face registration successful"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return render_template('register_face.html')

@auth_blueprint.route('/register_fingerprint', methods=['GET', 'POST'])
def register_fingerprint():
    if request.method == 'POST':
        try:
            # Process fingerprint data
            user_data = request.form.to_dict()
            
            # Save user data to Firebase
            get_db().collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'registration_methods': ['fingerprint'],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return jsonify({"status": "success", "message": "Fingerprint registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_fingerprint.html')

@auth_blueprint.route('/register_rfid', methods=['GET', 'POST'])
def register_rfid():
    if request.method == 'POST':
        try:
            # Process RFID data
            user_data = request.form.to_dict()
            rfid_code = user_data.get('rfid_code')
            
            # Save user data to Firebase
            get_db().collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'rfid_code': rfid_code,
                'registration_methods': ['rfid'],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return jsonify({"status": "success", "message": "RFID registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_rfid.html')

@auth_blueprint.route('/register_voice', methods=['GET', 'POST'])
def register_voice():
    if request.method == 'POST':
        try:
            # Process voice recognition data
            user_data = request.form.to_dict()
            voice_sample = request.files.get('voice_sample')
            
            # Save user data to Firebase
            get_db().collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'registration_methods': ['voice'],
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return jsonify({"status": "success", "message": "Voice registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_voice.html') 