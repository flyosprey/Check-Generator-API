import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import Config

if Config.ENVIRONMENT == "QA":
    SQLALCHEMY_DATABASE_URL = Config.QA_DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URL = Config.DATABASE_URL

DB_NAME = SQLALCHEMY_DATABASE_URL.split("/")[-1]

engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def create_database():
    conn = psycopg2.connect(
        dbname=Config.ADMIN_DB,
        user=Config.ADMIN_DB_USER,
        password=Config.ADMIN_DB_PASSWORD,
        host=Config.DB_HOST
    )
    conn.autocommit = True
    cur = conn.cursor()
    create_db_statement = sql.SQL('CREATE DATABASE {}').format(
        sql.Identifier(DB_NAME)
    )

    cur.execute(create_db_statement)

try:
    conn = psycopg2.connect(SQLALCHEMY_DATABASE_URL)
except psycopg2.OperationalError as e:
    if f"database \"{DB_NAME}\" does not exist" in str(e):
        create_database()
    else:
        raise e
