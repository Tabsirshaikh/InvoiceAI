import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import User
from db import get_db

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "1BF51B68996A1BA4EDB2F5D374424BB0D0EF79EFFB847D8CC1514D84E08C3D16")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# CryptContext is a password manager/configuration object.
# bcrypt is the password hashing algorithm.
# deprecated="auto" means if old hash formats exist,
# passlib can automatically migrate them.

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


# Tells FastAPI where login endpoint exists.
# Swagger UI uses this automatically.

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)


# ---------------------------------------------------------
# PASSWORD FUNCTIONS
# ---------------------------------------------------------

def verify_password(
    plain_password,
    hashed_password
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


def get_password_hash(password):
    return pwd_context.hash(password)


# ---------------------------------------------------------
# DATABASE FUNCTIONS
# ---------------------------------------------------------

# Given a username,
# find and return corresponding user from database.

def get_user(
    db: Session,
    username: str
):
    return (
        db.query(User)
        .filter(User.username == username)
        .first()
    )


# This function is the actual login checker.
#
# Username exists?
#         ↓
# Yes
#         ↓
# Password correct?
#         ↓
# Yes
#         ↓
# Return User
#
# Otherwise
#         ↓
# Return False

def authenticate_user(
    db: Session,
    username: str,
    password: str
):
    user = get_user(
        db,
        username
    )

    if user is None:
        return False

    if not verify_password(
        password,
        user.hashed_password
    ):
        return False

    return user


# ---------------------------------------------------------
# JWT TOKEN CREATION
# ---------------------------------------------------------

# User Login
#     │
#     ▼
# authenticate_user()
#     │
#     ▼
# User verified
#     │
#     ▼
# create_access_token()
#     │
#     ▼
# JWT Token generated
#     │
#     ▼
# Send token to frontend

def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    else:
        expire = (
            datetime.now(timezone.utc)
            + timedelta(minutes=15)
        )

    # Add expiration claim

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


# ---------------------------------------------------------
# JWT VALIDATION
# ---------------------------------------------------------

# Receives token from:
#
# Authorization:
# Bearer <jwt-token>
#
# Decodes JWT
# Extracts username
# Loads user from DB
# Returns current user

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username: str = payload.get("sub")

        if username is None:
            raise credential_exception

    except JWTError:
        raise credential_exception

    user = get_user(
        db,
        username
    )

    if user is None:
        raise credential_exception

    return user


# ---------------------------------------------------------
# ACTIVE USER CHECK
# ---------------------------------------------------------

# Runs after token verification.
#
# JWT Valid?
#      ↓
# Yes
#      ↓
# User disabled?
#      ↓
# No
#      ↓
# Allow access

async def get_current_active_user(
    current_user: User = Depends(
        get_current_user
    )
):
    if current_user.disable:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    
    return current_user