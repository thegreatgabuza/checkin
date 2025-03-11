import firebase_admin
from firebase_admin import credentials, firestore
import os
from datetime import datetime, timedelta

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate('firebase-key.json')
    firebase_admin.initialize_app(cred)

db = firestore.client()

# First test user data
test_user1 = {
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'test.user@example.com',
    'student_id': 'TEST123',
    'timestamp': firestore.SERVER_TIMESTAMP
}

# Second test user data
test_user2 = {
    'first_name': 'Jane',
    'last_name': 'Smith',
    'email': 'jane.smith@example.com',
    'student_id': 'JS456',
    'timestamp': firestore.SERVER_TIMESTAMP
}

# Create first user document with all auth methods
user1_ref = db.collection('users').document('test_user1')
user1_ref.set({
    **test_user1,
    'registration_methods': ['manual', 'facial', 'rfid', 'voice'],
    'rfid_code': 'TEST_RFID_123',
    'face_data': 'TEST_FACE_ENCODING',
    'voice_data': 'TEST_VOICE_SIGNATURE'
})

# Create second user document with different auth methods
user2_ref = db.collection('users').document('test_user2')
user2_ref.set({
    **test_user2,
    'registration_methods': ['facial', 'voice'],
    'face_data': 'TEST_FACE_ENCODING_2',
    'voice_data': 'TEST_VOICE_SIGNATURE_2'
})

# Create check-in records for first user
checkin1_ref = db.collection('checkins').document()
checkin1_ref.set({
    'student_id': test_user1['student_id'],
    'timestamp': firestore.SERVER_TIMESTAMP,
    'method': 'facial',
    'profile_created': True
})

# Create multiple check-in records for second user
base_time = datetime.now()
methods = ['facial', 'voice', 'facial']
for i, method in enumerate(methods):
    checkin_time = base_time - timedelta(hours=i*2)  # Create check-ins with different times
    checkin_ref = db.collection('checkins').document()
    checkin_ref.set({
        'student_id': test_user2['student_id'],
        'timestamp': checkin_time,
        'method': method,
        'profile_created': True
    })

print("Test users created successfully!")
print(f"User 1 - Student ID: {test_user1['student_id']}, Email: {test_user1['email']}")
print(f"User 2 - Student ID: {test_user2['student_id']}, Email: {test_user2['email']}")
print("You can now use these credentials to test the admin features.") 