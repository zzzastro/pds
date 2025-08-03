import firebase_admin

from firebase_admin import credentials, firestore

cred = credentials.Certificate(r"C:\Users\hp\Desktop\Code Projects\pds\plagiarism_detection_system\firebase_keys\serviceAccountKey.json")

firebase_admin.initialize_app(cred)

db = firestore.client()
