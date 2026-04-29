from firebase_config import firestore_db

# Write
ref = firestore_db.collection("_test").document("ping")
ref.set({"ok": True})

# Read back
doc = ref.get()
print(doc.to_dict())

# Clean up
ref.delete()
