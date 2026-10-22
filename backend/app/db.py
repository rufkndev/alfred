import datetime as dt
import os
from zoneinfo import ZoneInfo

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

TZ = os.environ.get("TZ", "Europe/Moscow")

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
Session = sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with Session() as db:
        yield db


def now():
    return dt.datetime.now(ZoneInfo(TZ))


def today():
    return now().date()
