from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
import bcrypt

from app.db.database import get_db
from app.db.models.user import User
from app.core.security import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# -----------------------------
# REGISTER REQUEST BODY
# -----------------------------
class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


# -----------------------------
# REGISTER
# -----------------------------
@router.post("/register", status_code=201)
def register_user(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    name = data.name.strip()
    email = data.email.strip().lower()
    password = data.password

    # Name validation
    if len(name) < 2:
        raise HTTPException(
            status_code=400,
            detail="Name must contain at least 2 characters"
        )

    # Basic email validation
    if "@" not in email or "." not in email:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address"
        )

    # Password validation
    if len(password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 8 characters"
        )

    # Duplicate user check
    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    new_user = User(
        name=name,
        email=email,
        password=hashed_password,
        role="user",
        is_active=True
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "is_active": new_user.is_active,
        "message": "User registered successfully"
    }


# -----------------------------
# LOGIN
# -----------------------------
@router.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username.strip().lower()
    password = form_data.password

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account inactive"
        )

    password_valid = bcrypt.checkpw(
        password.encode("utf-8"),
        user.password.encode("utf-8")
    )

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }