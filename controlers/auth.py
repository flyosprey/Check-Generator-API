from datetime import timedelta

from fastapi import Depends, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
from schemas.auth_schema import CreateUser
from utils.exceptions import get_user_exception, token_exception, bad_request_exception
from utils.utils import get_db
from services.auth_service import get_current_user, authenticate_user, create_access_token, create_user, delete_user

from config import Config


router = APIRouter(
    prefix="",
    tags=["auth"],
    responses={401: {"user": "Not authorized"}}
)


@router.post("/sign-up/", status_code=status.HTTP_201_CREATED)
async def registration(user_data: CreateUser, db: Session = Depends(get_db)):
    if db.query(models.Users).filter(models.Users.email == user_data.email).first():
        raise bad_request_exception(detail="The email already exist")
    if db.query(models.Users).filter(models.Users.username == user_data.username).first():
        raise bad_request_exception(detail="The username already exist")

    user_id = create_user(user_data=user_data, db=db)

    return {"detail": "Created", "user_id": user_id}


@router.delete("/unsubscribe/", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(db: Session = Depends(get_db), user: dict = Depends(get_current_user)):
    if user is None:
        raise get_user_exception()

    delete_user(user_id=user["id"], db=db)


@router.post("/login/", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise token_exception()

    token_expires = timedelta(minutes=int(Config.TOKEN_EXPIRATION_MINUTES))
    token = create_access_token(user.username, user.id, expires_delta=token_expires)

    return {'access_token': token, 'token_type': 'bearer'}
