import os
import json
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def initialize_firestore():
    """Initialize Firebase using environment variables instead of file."""
    try:
        # Get credentials from environment variables
        service_account_info = {
            "type": os.getenv("FIREBASE_TYPE"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
            "universe_domain": "googleapis.com"
        }
        
        # Create credentials from service account info
        cred = credentials.Certificate(service_account_info)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
    except Exception as e:
        print(f"Error initializing Firebase: {e}")

# Upload submission to Firestore
def upload_submission(collection_name, document_id, data):
    try:
        db = firestore.client()
        db.collection(collection_name).document(document_id).set(data)
        print(f'Document {document_id} added to collection {collection_name}.')
    except Exception as e:
        print(f"Error uploading document to Firestore: {e}")

# Retrieve submissions from Firestore
def retrieve_submissions(collection_name):
    try:
        db = firestore.client()
        submissions = db.collection(collection_name).stream()
        return {doc.id: doc.to_dict() for doc in submissions}
    except Exception as e:
        print(f"Error retrieving submissions: {e}")
        return {}