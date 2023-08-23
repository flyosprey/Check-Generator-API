from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, status, APIRouter, Security
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session, joinedload
from passlib.context import CryptContext

import models
from schemas.auth import CreateUser
from utils.exceptions import get_user_exception, token_exception, bad_request_exception
from utils.utils import get_db
from database import engine

from config import Config


SECRET_KEY = Config.SECRET_KEY
ALGORITHM = Config.ALGORITHM


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token/")
models.Base.metadata.create_all(bind=engine)


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


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


@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_new_user(create_user: CreateUser, db: Session = Depends(get_db)):
    if db.query(models.Users).filter(models.Users.email == create_user.email).first():
        raise bad_request_exception(detail="The email already exist")
    if db.query(models.Users).filter(models.Users.username == create_user.username).first():
        raise bad_request_exception(detail="The username already exist")

    create_user_model = models.Users()
    create_user_model.email = create_user.email
    create_user_model.username = create_user.username
    create_user_model.hashed_password = get_password_hash(create_user.password)
    create_user_model.is_active = True

    db.add(create_user_model)
    db.commit()

    return {"detail": "Created", "user_id": create_user_model.id}


@router.delete("/users/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()
    user_to_delete = db.query(models.Users).options(joinedload(models.Users.checks)).get(user["id"])

    db.delete(user_to_delete)
    db.commit()


@router.post("/token/", status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise token_exception()
    token_expires = timedelta(minutes=20)
    token = create_access_token(user.username, user.id, expires_delta=token_expires)

    return {'access_token': token, 'token_type': 'bearer'}
