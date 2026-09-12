import os
import firebase_admin
from firebase_admin import credentials, firestore


def _get_service_account_path():
    """Return the service account path, preferring the FIRESTORE_CREDENTIALS
    env var so the key never needs to live inside the repo."""
    env_path = os.environ.get('FIRESTORE_CREDENTIALS', '').strip()
    if env_path:
        return env_path
    return os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')


SERVICE_ACCOUNT_PATH = _get_service_account_path()

if os.environ.get('FIRESTORE_EMULATOR_HOST'):
    firebase_admin.initialize_app()
else:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()