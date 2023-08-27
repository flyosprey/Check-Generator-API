from datetime import datetime, timedelta
from typing import Optional

from fastapi import Security
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy.orm import joinedload

import models
from utils.exceptions import get_user_exception

from config import Config


SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/login/")
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password):
    return bcrypt_context.hash(password)


def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users)\
        .filter(models.Users.username == username)\
        .first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(username: str, user_id: int, expires_delta: Optional[timedelta] = None):
    encode = {"sub": username, "id": user_id}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    encode.update({"exp": expire})

    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Security(oauth2_bearer)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise get_user_exception()

        return {"username": username, "id": user_id}
    except JWTError:
        raise get_user_exception()


async def create_user(user_data, db) -> int:
    create_user_model = models.Users()
    create_user_model.email = user_data.email
    create_user_model.username = user_data.username
    create_user_model.hashed_password = get_password_hash(user_data.password)
    create_user_model.is_active = True

    db.add(create_user_model)
    db.commit()

    return create_user_model.id


async def delete_user(user_id: int, db):
    user_to_delete = db.query(models.Users).options(joinedload(models.Users.checks)).get(user_id)

    db.delete(user_to_delete)
    db.commit()
