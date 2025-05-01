import firebase_admin
from firebase_admin import auth, credentials, exceptions
from fastapi import HTTPException, status
from app.core.config import settings


# Singleton pattern for Firebase initialization
_firebase_app = None

def initialize_firebase():
    global _firebase_app
    try:
        if not _firebase_app:
            cred = credentials.Certificate(settings.FIREBASE_SA_KEY_PATH)
            _firebase_app = firebase_admin.initialize_app(cred)
        return _firebase_app
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Firebase initialization failed: {str(e)}"
        )

# Initialize on import
initialize_firebase()

async def create_firebase_user(email: str, password: str):
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        return user.uid
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

async def verify_firebase_login(email: str, password: str):
    try:
        user = auth.get_user_by_email(email)
        # This is just to verify the user exists - actual auth happens client side
        return user.uid
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )