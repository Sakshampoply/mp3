from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import firebase_admin
from firebase_admin import auth, credentials, exceptions
from app.db.postgres_client import get_db
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, FirebaseLogin, Token
import requests
from app.core.config import settings

router = APIRouter()
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    if not credentials.scheme == "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")
        
    token = credentials.credentials
    try:
        # Add debug logging
        print(f"Verifying token: {token[:50]}...")  # Log first 50 chars
        
        decoded = auth.verify_id_token(token)
        print(f"Decoded UID: {decoded['uid']}")
        
        user = db.query(User).filter(User.id == decoded['uid']).first()
        if not user:
            raise HTTPException(404, "User not found in database")
            
        return user
        
    except auth.ExpiredIdTokenError:
        raise HTTPException(401, "Token expired")
    except auth.InvalidIdTokenError:
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        print(f"Auth error: {str(e)}")
        raise HTTPException(500, "Authentication failed")
        

def require_role(required_role: UserRole):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        # Create Firebase user
        user = auth.create_user(
            email=user_data.email,
            password=user_data.password
        )
        
        # Create local user
        db_user = User(
            id=user.uid,
            email=user_data.email,
            role=UserRole(user_data.role)
        )
        
        db.add(db_user)
        db.commit()
        return {"message": "User created successfully"}
        
    except auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )

@router.post("/login", response_model=Token)
async def login_user(login_data: FirebaseLogin):
    """Authenticate using Firebase REST API"""
    try:
        response = requests.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIREBASE_API_KEY}",
            json={
                "email": login_data.email,
                "password": login_data.password,
                "returnSecureToken": True
            }
        )
        response.raise_for_status()
        
        data = response.json()
        return {
            "access_token": data["idToken"],  # Correct token field
            "token_type": "bearer"
        }
    except requests.HTTPError as e:
        error = e.response.json().get("error", {})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.get("message", "Authentication failed")
        )