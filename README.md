# Student Check-in System

A Flask web application for student check-in with multiple authentication methods including RFID card scanning, facial recognition (using LandingAI), fingerprint, voice recognition, and manual entry.

## Features

- **Multiple Authentication Methods**:
  - RFID Card Scanning
  - Facial Recognition (using LandingAI)
  - Fingerprint Authentication
  - Voice Recognition
  - Manual Entry

- **Animated UI**: Beautiful blue-themed animated interface with changing backgrounds

- **Firebase Integration**: User data and authentication details stored in Firebase

- **Voice Registration**: Support for voice recognition with suggested registration phrases

- **Facial Registration**: Captures multiple angles for better recognition and sends to LandingAI for training

## Setup and Installation

### Prerequisites

- Python 3.7+
- Firebase account
- (Optional) LandingAI account for facial recognition
- (Optional) RFID reader hardware

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/student-checkin.git
   cd student-checkin
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a Firebase project and download your service account key file:
   - Rename it to `firebase-key.json` and place it in the project root
   - Or set the path in environment variables

5. Create a `.env` file with your configuration:
   ```
   SECRET_KEY=your-secret-key
   FIREBASE_KEY_PATH=path/to/firebase-key.json
   LANDING_AI_API_KEY=your-landing-ai-api-key
   LANDING_AI_PROJECT_ID=your-landing-ai-project-id
   ```

6. Run the application:
   ```
   python app.py
   ```

7. Access the application at `http://localhost:5000`

## Project Structure

```
student-checkin/
├── app.py                    # Main Flask application
├── routes/                   # Route blueprints
│   ├── auth_routes.py        # Authentication routes
│   └── landing_ai_routes.py  # LandingAI integration routes
├── static/                   # Static files
│   ├── css/                  # CSS files
│   ├── js/                   # JavaScript files
│   └── images/               # Image files
├── templates/                # HTML templates
│   ├── base.html             # Base template
│   ├── index.html            # Home page
│   ├── scan.html             # Card scanning page
│   ├── register.html         # Registration options
│   ├── register_face.html    # Facial registration
│   └── register_voice.html   # Voice registration
├── requirements.txt          # Python dependencies
└── firebase-key.json         # Firebase credentials
```

## Usage

1. Open the application in your browser
2. Choose your preferred authentication method
3. Follow the on-screen instructions to register or check in

## Development

### Adding New Authentication Methods

1. Create a new route in `routes/auth_routes.py`
2. Create a new template in the `templates` directory
3. Add the authentication logic and Firebase integration

### Firebase Integration

The application uses Firebase for data storage. The schema includes:

- **users**: Collection storing user information
  - first_name: User's first name
  - last_name: User's last name
  - email: User's email
  - student_id: Student ID number
  - registration_method: Method used to register (facial, voice, rfid, etc.)
  - timestamp: Registration timestamp

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Flask: Web framework
- Firebase: Database and authentication
- LandingAI: Facial recognition capabilities 