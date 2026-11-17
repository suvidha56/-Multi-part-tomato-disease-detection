
from flask import Blueprint, request, jsonify
import datetime
import requests
from config import Config

contact_bp = Blueprint('contact', __name__)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz5nZRaUz2dbryaFHYQjKnqJQ-hubAA4K_25GUqoAJT78_PDXfRw6Bvyy8Rs8cbdW0Pag/exec"


@contact_bp.route('/contact', methods=['POST'])
def submit_contact():

    data = request.get_json() or {}

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    subject = data.get('subject', '').strip()
    message = data.get('message', '').strip()

    if not name or not email or not message:
        return jsonify({
            'error': 'Name, email, and message are required'
        }), 400

    contact_entry = {
        'name': name,
        'email': email,
        'subject': subject,
        'message': message,
        'created_at': datetime.datetime.now().isoformat()
    }

    # Send data to Google Sheets
    try:
        response = requests.post(
            GOOGLE_SCRIPT_URL,
            json=contact_entry,
            timeout=20
        )

        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            raise Exception(result.get('error', 'Google Sheets error'))

    except Exception as e:
        print("Google Sheets error:", e)
        return jsonify({
            'status': 'error',
            'message': 'Unable to save contact message'
        }), 500

    # Save in MongoDB if available
    try:
        from pymongo import MongoClient

        client = MongoClient(
            Config.MONGO_URI,
            serverSelectionTimeoutMS=2000
        )
        db = client.get_default_database('agri_ai')
        db.contact_messages.insert_one(contact_entry)
        client.close()

    except Exception as e:
        print("MongoDB unavailable:", e)

    return jsonify({
        'status': 'success',
        'message': 'Message sent successfully. Thank you for contacting Agri AI.'
    }), 200
