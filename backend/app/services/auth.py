from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, SECRET_KEY
from app.db.session import get_db
from app.models.entities import User


ADMIN_RH = "ADMIN_RH"
ANALYSTE_RH = "ANALYSTE_RH"
MANAGER_RH = "MANAGER_RH"
DIRIGEANT = "DIRIGEANT"
ALL_ROLES = (ADMIN_RH, ANALYSTE_RH, MANAGER_RH, DIRIGEANT)

DEMO_USERS = [
    ("admin.rh@demo.local", "Administrateur RH", "Admin123!", ADMIN_RH),
    ("analyste.rh@demo.local", "Analyste RH", "Analyste123!", ANALYSTE_RH),
    ("manager.rh@demo.local", "Manager RH", "Manager123!", MANAGER_RH),
    ("dirigeant.rh@demo.local", "Dirigeant RH", "Dirigeant123!", DIRIGEANT),
]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "fullName": user.full_name,
        "role": user.role,
    }


def create_access_token(user: User) -> str:
    expires_at = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.email,
        "role": user.role,
        "exp": expires_at,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification requise.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        if not isinstance(email, str):
            raise credentials_exception
    except JWTError as error:
        raise credentials_exception from error

    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_roles(*allowed_roles: str):
    allowed = set(allowed_roles)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès refusé pour ce rôle.",
            )
        return current_user

    return dependency


def seed_demo_users(db: Session, users: Iterable[tuple[str, str, str, str]] = DEMO_USERS) -> None:
    if db.query(User).count():
        return

    for email, full_name, password, role in users:
        db.add(
            User(
                email=email.lower(),
                full_name=full_name,
                hashed_password=hash_password(password),
                role=role,
                is_active=True,
            )
        )
    db.commit()
