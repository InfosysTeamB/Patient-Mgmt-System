from dataclasses import dataclass
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from firebase_config import db

TOKENS_COL = 'tokens'


@dataclass
class FakeUser:
    """Minimal user object that satisfies DRF's request.user contract."""
    id: str
    role: str
    entity_id: str

    @property
    def is_authenticated(self):
        return True


class FirebaseTokenAuthentication(BaseAuthentication):
    """Authenticates requests using an opaque token stored in Firestore.

    Expected header format:  Authorization: Token <token>
    """

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            return None

        token = auth_header.split(' ', 1)[1].strip()
        if not token:
            return None

        token_doc = db.collection(TOKENS_COL).document(token).get()
        if not token_doc.exists:
            raise AuthenticationFailed('Invalid or expired token')

        data = token_doc.to_dict()
        user = FakeUser(
            id=data.get('user_id', ''),
            role=data.get('role', ''),
            entity_id=data.get('entity_id', ''),
        )
        return (user, token)

    def authenticate_header(self, request):
        return 'Token'