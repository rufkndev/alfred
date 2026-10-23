import datetime as dt
import os
from decimal import Decimal
from pathlib import Path

from sqlalchemy import JSON, Date, DateTime, ForeignKey, LargeBinary, Numeric, String, Text, func, select
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base

Created = lambda: mapped_column(DateTime(timezone=True), server_default=func.now())  # noqa: E731


class Item(Base):
    """Строка списка: задачи дня, блоки дня, задачи разделов, установки."""
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    list: Mapped[str] = mapped_column(String(64), index=True)
    date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    text: Mapped[str] = mapped_column(Text)
    done: Mapped[bool] = mapped_column(default=False)
    archived: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[dt.datetime] = Created()


class Note(Base):
    __tablename__ = "notes"
    id: Mapped[int] = mapped_column(primary_key=True)
    list: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[dt.datetime] = Created()
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Doc(Base):
    """Документ по ключу: мысли дня, память ИИ, планы."""
    __tablename__ = "docs"
    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    text: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Business(Base):
    __tablename__ = "businesses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    archived: Mapped[bool] = mapped_column(default=False)
    position: Mapped[int] = mapped_column(default=0)


class Expense(Base):
    __tablename__ = "expenses"
    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(16))  # regular | subscription
    name: Mapped[str] = mapped_column(String(256))
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    every_n: Mapped[int] = mapped_column(default=1)
    unit: Mapped[str] = mapped_column(String(8), default="month")  # day | week | month
    note: Mapped[str] = mapped_column(Text, default="")


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    archived: Mapped[bool] = mapped_column(default=False)


class Balance(Base):
    __tablename__ = "balances"
    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    created_at: Mapped[dt.datetime] = Created()


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat: Mapped[str] = mapped_column(String(32), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant | tool | reset
    content: Mapped[str] = mapped_column(Text, default="")
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[dt.datetime] = Created()


class Reminder(Base):
    __tablename__ = "reminders"
    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    sent: Mapped[bool] = mapped_column(default=False)


class PushSub(Base):
    __tablename__ = "push_subs"
    id: Mapped[int] = mapped_column(primary_key=True)
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(Text)
    auth: Mapped[str] = mapped_column(Text)


class AuthSession(Base):
    __tablename__ = "sessions"
    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[dt.datetime] = Created()


class Credential(Base):
    __tablename__ = "webauthn_creds"
    id: Mapped[str] = mapped_column(String(512), primary_key=True)  # base64url
    public_key: Mapped[bytes] = mapped_column(LargeBinary)
    sign_count: Mapped[int] = mapped_column(default=0)


SEED_DIR = Path(os.environ.get("SEED_DIR", "/srv/seed"))


def seed(db):
    if db.scalar(select(func.count(Business.id))) == 0:
        for i, name in enumerate(["BBifather", "MentorLM", "Pixora", "YC"]):
            db.add(Business(name=name, position=i))
    # seed/memory.gym.md → документ memory:gym; заполняется только пока документ пуст
    for f in sorted(SEED_DIR.glob("*.md")) if SEED_DIR.is_dir() else []:
        key = f.stem.replace(".", ":")
        doc = db.get(Doc, key)
        if not doc or not doc.text.strip():
            db.merge(Doc(key=key, text=f.read_text(encoding="utf-8")))
    db.commit()
