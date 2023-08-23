from pydantic import BaseModel


class CreateUser(BaseModel):
    username: str
    email: str
    password: str
