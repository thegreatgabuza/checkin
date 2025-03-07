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