import base64
import json
import os
import sys
import time

from fastapi import APIRouter, Body, Depends
from pywebpush import WebPushException, webpush
from sqlalchemy import select

from .auth import require_auth
from .db import Session, get_db, now
from .models import PushSub, Reminder

VAPID_PUBLIC = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_SUB = os.environ.get("VAPID_SUB", "mailto:admin@bbifather.site")

router = APIRouter(prefix="/api/push", dependencies=[Depends(require_auth)])


@router.get("/key")
def key():
    return {"key": VAPID_PUBLIC}


@router.post("/subscribe")
def subscribe(data: dict = Body(...), db=Depends(get_db)):
    sub = db.scalar(select(PushSub).filter_by(endpoint=data["endpoint"])) or PushSub(endpoint=data["endpoint"])
    sub.p256dh, sub.auth = data["keys"]["p256dh"], data["keys"]["auth"]
    db.add(sub)
    db.commit()
    return {"ok": True}


@router.post("/test")
def test(db=Depends(get_db)):
    send_all(db, "Alfred", "Уведомления работают")
    db.commit()
    return {"ok": True}


def send_all(db, title, body):
    for s in db.scalars(select(PushSub)).all():
        try:
            webpush({"endpoint": s.endpoint, "keys": {"p256dh": s.p256dh, "auth": s.auth}},
                    json.dumps({"title": title, "body": body}, ensure_ascii=False),
                    vapid_private_key=VAPID_PRIVATE, vapid_claims={"sub": VAPID_SUB})
        except WebPushException as e:
            if e.response is not None and e.response.status_code in (404, 410):
                db.delete(s)
            else:
                print("push:", e, flush=True)


def loop():
    """Раз в 30 секунд отправляет наступившие напоминания."""
    while True:
        try:
            with Session() as db:
                for r in db.scalars(select(Reminder).where(Reminder.sent.is_(False), Reminder.at <= now())).all():
                    send_all(db, "Alfred", r.text)
                    r.sent = True
                db.commit()
        except Exception as e:
            print("reminders:", e, flush=True)
        time.sleep(30)


def generate_keys():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()  # noqa: E731
    key = ec.generate_private_key(ec.SECP256R1())
    print("VAPID_PUBLIC_KEY=" + b64(key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)))
    print("VAPID_PRIVATE_KEY=" + b64(key.private_numbers().private_value.to_bytes(32, "big")))


if __name__ == "__main__" and sys.argv[1:] == ["keys"]:
    generate_keys()
