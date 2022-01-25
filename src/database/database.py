import json
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from ..config import SQLITE_FILE_PATH

db_path = os.path.dirname(SQLITE_FILE_PATH)
if not os.path.exists(db_path):
    os.mkdir(db_path)
SQLALCHEMY_DATABASE_URL = f"sqlite:///{SQLITE_FILE_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
    # echo=True
)
Session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Base = declarative_base()
