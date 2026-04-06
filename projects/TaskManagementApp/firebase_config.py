import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account_key.json")
    firebase_admin.initialize_app(cred)

firestore_db = firestore.client()