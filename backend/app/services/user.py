from sqlalchemy.orm import Session

import bcrypt as _bcrypt
if not hasattr(_bcrypt, "__about__"):
    _bcrypt.__about__ = type("about", (), {"__version__": _bcrypt.__version__})()

from passlib.context import CryptContext
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user_data: UserCreate):
    hashed = pwd_context.hash(user_data.password)
    user = User(
        username=user_data.username, password_hash=hashed, role=user_data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, user_data: UserUpdate):
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.password is not None:
        user.password_hash = pwd_context.hash(user_data.password)
    if user_data.role is not None:
        user.role = user_data.role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
