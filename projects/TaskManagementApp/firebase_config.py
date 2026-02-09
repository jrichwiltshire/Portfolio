import os
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase_service_account_key.json")
firestore_db = firestore.client()
