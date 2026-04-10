import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

if not firebase_admin._apps:
    service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if service_account_json:
        cred = credentials.Certificate(json.loads(service_account_json))
    else:
        cred = credentials.Certificate("firebase_service_account_key.json")
    firebase_admin.initialize_app(cred)

firestore_db = firestore.client()