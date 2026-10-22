import os
import secrets
import time
from urllib.parse import urlparse

import webauthn
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorAttachment,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .db import TZ, get_db
from .models import AuthSession, Credential

PIN = os.environ.get("ALFRED_PIN", "")
ORIGIN = os.environ.get("ORIGIN", "http://localhost:8100")
RP_ID = urlparse(ORIGIN).hostname
COOKIE = "sid"

fails = {"n": 0, "until": 0.0}
challenges: dict[str, bytes] = {}

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


def creds(db):
    return [PublicKeyCredentialDescriptor(id=base64url_to_bytes(c.id)) for c in db.scalars(select(Credential))]


@router.get("/status")
def status(request: Request, db=Depends(get_db)):
    return {"authed": session_ok(request, db), "faceid": db.scalar(select(func.count(Credential.id))) > 0, "tz": TZ}


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


@router.post("/webauthn/register/options", dependencies=[Depends(require_auth)])
def register_options(db=Depends(get_db)):
    opts = webauthn.generate_registration_options(
        rp_id=RP_ID, rp_name="Alfred", user_name="alfred", user_id=b"alfred-owner",
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=creds(db),
    )
    challenges["reg"] = opts.challenge
    return Response(webauthn.options_to_json(opts), media_type="application/json")


@router.post("/webauthn/register/verify", dependencies=[Depends(require_auth)])
def register_verify(data: dict = Body(...), db=Depends(get_db)):
    try:
        v = webauthn.verify_registration_response(
            credential=data, expected_challenge=challenges.pop("reg", b""),
            expected_rp_id=RP_ID, expected_origin=ORIGIN, require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(400, f"Face ID: {e}")
    db.add(Credential(id=bytes_to_base64url(v.credential_id), public_key=v.credential_public_key,
                      sign_count=v.sign_count))
    db.commit()
    return {"ok": True}


@router.post("/webauthn/login/options")
def login_options(db=Depends(get_db)):
    opts = webauthn.generate_authentication_options(
        rp_id=RP_ID, allow_credentials=creds(db), user_verification=UserVerificationRequirement.REQUIRED,
    )
    challenges["auth"] = opts.challenge
    return Response(webauthn.options_to_json(opts), media_type="application/json")


@router.post("/webauthn/login/verify")
def login_verify(request: Request, response: Response, data: dict = Body(...), db=Depends(get_db)):
    cred = db.get(Credential, data.get("id", ""))
    if not cred:
        raise HTTPException(400, "Face ID не зарегистрирован")
    try:
        v = webauthn.verify_authentication_response(
            credential=data, expected_challenge=challenges.pop("auth", b""),
            expected_rp_id=RP_ID, expected_origin=ORIGIN,
            credential_public_key=cred.public_key, credential_current_sign_count=cred.sign_count,
            require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(400, f"Face ID: {e}")
    cred.sign_count = v.new_sign_count
    db.commit()
    login(request, response, db)
    return {"ok": True}
