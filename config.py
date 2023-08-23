from decouple import config


class Config:
    DATABASE_URL = config("DATABASE_URL")
    SECRET_KEY = config("SECRET_KEY")
    ALGORITHM = config("ALGORITHM")
    QA_DATABASE_URL = config("QA_DATABASE_URL")
    ENVIRONMENT = config("ENVIRONMENT")
    ADMIN_DB = config("ADMIN_DB")
    ADMIN_DB_USER = config("ADMIN_DB_USER")
    ADMIN_DB_PASSWORD = config("ADMIN_DB_PASSWORD")
    DB_HOST = config("DB_HOST")
