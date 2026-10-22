import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from . import ai, api, auth, push
from .db import Base, Session, engine
from .models import seed

STATIC = (Path(__file__).parent.parent / "static").resolve()


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(engine)
    with Session() as db:
        seed(db)
    threading.Thread(target=push.loop, daemon=True).start()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
for module in (auth, api, ai, push):
    app.include_router(module.router)


@app.get("/{path:path}")
def frontend(path: str):
    if path.startswith("api/"):
        raise HTTPException(404)
    f = (STATIC / path).resolve()
    if path and f.is_file() and f.is_relative_to(STATIC):
        cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else "no-cache"
        return FileResponse(f, headers={"Cache-Control": cache})
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
