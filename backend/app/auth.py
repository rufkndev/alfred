import os
import secrets
import time

from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response

from .db import TZ, get_db
from .models import AuthSession

PIN = os.environ.get("ALFRED_PIN", "")
ORIGIN = os.environ.get("ORIGIN", "http://localhost:8100")
COOKIE = "sid"

fails = {"n": 0, "until": 0.0}

router = APIRouter(prefix="/api/auth")


def session_ok(request: Request, db) -> bool:
    token = request.cookies.get(COOKIE)
    return bool(token and db.get(AuthSession, token))


def require_auth(request: Request, db=Depends(get_db)):
    if not session_ok(request, db):
        raise HTTPException(401)


def login(request: Request, response: Response, db):
    if session_ok(request, db):
        return
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token=token))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=365 * 86400, httponly=True, samesite="lax",
                        secure=ORIGIN.startswith("https"))


@router.get("/status")
def status(request: Request, db=Depends(get_db)):
    return {"authed": session_ok(request, db), "tz": TZ}


@router.post("/pin")
def pin(request: Request, response: Response, data: dict = Body(...), db=Depends(get_db)):
    if time.time() < fails["until"]:
        raise HTTPException(429, "Слишком много попыток, подожди 15 минут")
    if not PIN or not secrets.compare_digest(str(data.get("pin", "")), PIN):
        fails["n"] += 1
        if fails["n"] >= 5:
            fails.update(n=0, until=time.time() + 900)
        raise HTTPException(403, "Неверный PIN")
    fails["n"] = 0
    login(request, response, db)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response, db=Depends(get_db)):
    session = db.get(AuthSession, request.cookies.get(COOKIE, ""))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie(COOKIE)
    return {"ok": True}

