from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import firebase_admin
from firebase_admin import firestore
import json
import os

auth_blueprint = Blueprint('auth', __name__, url_prefix='/auth')
db = firestore.client()

@auth_blueprint.route('/register_manual', methods=['GET', 'POST'])
def register_manual():
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            # Save user data to Firebase
            db.collection('users').add({
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'email': data.get('email'),
                'student_id': data.get('student_id'),
                'registration_method': 'manual',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            return jsonify({"status": "success", "message": "User registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_manual.html')

@auth_blueprint.route('/check_student_id', methods=['POST'])
def check_student_id():
    try:
        data = request.json
        student_id = data.get('student_id')

        if not student_id or not student_id.startswith('2') or len(student_id) != 8:
            return jsonify({"status": "error", "message": "Invalid Student ID"})

        # Check if student already exists in Firestore
        user_ref = db.collection('users').document(student_id).get()
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
            user_ref = db.collection('users').document(student_id).get()
            if user_ref.exists:
                return jsonify({"status": "exists", "message": "Student already registered"})

            # If student does not exist, ask for additional info
            first_name = data.get('first_name')
            last_name = data.get('last_name')

            if not first_name or not last_name:
                return jsonify({"status": "need_more_info", "message": "Please provide first name and last name."})

            # Save new student to Firestore
            db.collection('users').document(student_id).set({
                'first_name': first_name,
                'last_name': last_name,
                'email': f"{student_id}@dut4life.ac.za",
                'student_id': student_id,
                'registration_method': 'barcode',
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
            # Process facial recognition data
            user_data = request.form.to_dict()
            face_image = request.files.get('face_image')
            
            # Save user data to Firebase
            user_ref = db.collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'registration_method': 'facial',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            # LandingAI integration will go here
            # This is a placeholder for the actual implementation
            
            return jsonify({"status": "success", "message": "Face registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_face.html')

@auth_blueprint.route('/register_fingerprint', methods=['GET', 'POST'])
def register_fingerprint():
    if request.method == 'POST':
        try:
            # Process fingerprint data
            user_data = request.form.to_dict()
            
            # Save user data to Firebase
            db.collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'registration_method': 'fingerprint',
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
            db.collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'rfid_code': rfid_code,
                'registration_method': 'rfid',
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
            db.collection('users').add({
                'first_name': user_data.get('first_name'),
                'last_name': user_data.get('last_name'),
                'email': user_data.get('email'),
                'student_id': user_data.get('student_id'),
                'registration_method': 'voice',
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return jsonify({"status": "success", "message": "Voice registered successfully"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)})
    return render_template('register_voice.html') 