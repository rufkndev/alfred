import datetime as dt

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import delete, func, select, update

from .auth import require_auth
from .db import get_db, today
from .models import Account, Balance, Business, Doc, Expense, Item, Message, Note, Section

router = APIRouter(prefix="/api", dependencies=[Depends(require_auth)])

ITEM_FIELDS = ("text", "done", "archived", "date")
NOTE_FIELDS = ("title", "body")
EXPENSE_FIELDS = ("kind", "name", "amount", "every_n", "unit", "note")
SECTION_TABS = ("tasks", "notes", "mindsets", "plan")


def row(obj):
    return {c.key: getattr(obj, c.key) for c in obj.__table__.columns}


def apply(obj, data, fields):
    for f in fields:
        if f in data:
            v = data[f]
            if f == "date" and isinstance(v, str):
                v = dt.date.fromisoformat(v)
            setattr(obj, f, v)
    return obj


def get_or_404(db, model, id):
    obj = db.get(model, id)
    if not obj:
        raise HTTPException(404)
    return obj


def next_pos(db, model, **filters):
    return (db.scalar(select(func.max(model.position)).filter_by(**filters)) or 0) + 1


def rollover(db):
    """Невыполненные задачи прошлых дней переезжают на сегодня."""
    db.execute(update(Item).where(Item.list == "day_tasks", Item.date < today(), Item.done.is_(False))
               .values(date=today()))
    db.commit()


def items_query(list_, date=None):
    q = select(Item).filter_by(list=list_)
    if date:
        q = q.filter_by(date=dt.date.fromisoformat(date) if isinstance(date, str) else date)
    return q.order_by(Item.position, Item.id)


def add_item(db, list_, text, date=None):
    d = dt.date.fromisoformat(date) if isinstance(date, str) else date
    item = Item(list=list_, text=text, date=d, position=next_pos(db, Item, list=list_, date=d))
    db.add(item)
    db.commit()
    return item


def accounts_view(db):
    out = []
    for a in db.scalars(select(Account).filter_by(archived=False).order_by(Account.id)):
        history = db.scalars(select(Balance).filter_by(account_id=a.id).order_by(Balance.id.desc()).limit(30)).all()
        out.append({"id": a.id, "name": a.name, "amount": history[0].amount if history else 0,
                    "history": [{"amount": b.amount, "created_at": b.created_at} for b in history]})
    return out


# --- items ---

@router.get("/items")
def list_items(list_: str = Query(alias="list"), date: str | None = None, db=Depends(get_db)):
    if list_ == "day_tasks":
        rollover(db)
    return [row(i) for i in db.scalars(items_query(list_, date))]


@router.post("/items")
def create_item(data: dict = Body(...), db=Depends(get_db)):
    return row(add_item(db, data["list"], data["text"], data.get("date")))


@router.patch("/items/{id}")
def patch_item(id: int, data: dict = Body(...), db=Depends(get_db)):
    item = apply(get_or_404(db, Item, id), data, ITEM_FIELDS)
    db.commit()
    return row(item)


@router.delete("/items/{id}")
def delete_item(id: int, db=Depends(get_db)):
    db.execute(delete(Item).filter_by(id=id))
    db.commit()
    return {"ok": True}


@router.post("/items/reorder")
def reorder_items(data: dict = Body(...), db=Depends(get_db)):
    for pos, id in enumerate(data["ids"]):
        db.execute(update(Item).filter_by(id=id).values(position=pos))
    db.commit()
    return {"ok": True}


# --- notes ---

@router.get("/notes")
def list_notes(list_: str = Query(alias="list"), db=Depends(get_db)):
    return [row(n) for n in db.scalars(select(Note).filter_by(list=list_).order_by(Note.updated_at.desc()))]


@router.get("/notes/{id}")
def get_note(id: int, db=Depends(get_db)):
    return row(get_or_404(db, Note, id))


@router.post("/notes")
def create_note(data: dict = Body(...), db=Depends(get_db)):
    note = apply(Note(list=data["list"]), data, NOTE_FIELDS)
    db.add(note)
    db.commit()
    return row(note)


@router.patch("/notes/{id}")
def patch_note(id: int, data: dict = Body(...), db=Depends(get_db)):
    note = apply(get_or_404(db, Note, id), data, NOTE_FIELDS)
    db.commit()
    return row(note)


@router.delete("/notes/{id}")
def delete_note(id: int, db=Depends(get_db)):
    db.execute(delete(Note).filter_by(id=id))
    db.commit()
    return {"ok": True}


# --- docs (мысли дня, память, планы) ---

@router.get("/docs/{key:path}")
def get_doc(key: str, db=Depends(get_db)):
    doc = db.get(Doc, key)
    return {"key": key, "text": doc.text if doc else ""}


@router.put("/docs/{key:path}")
def put_doc(key: str, data: dict = Body(...), db=Depends(get_db)):
    doc = db.get(Doc, key) or Doc(key=key)
    doc.text = data["text"]
    db.add(doc)
    db.commit()
    return {"key": key, "text": doc.text}


# --- businesses ---

@router.get("/businesses")
def list_businesses(db=Depends(get_db)):
    return [row(b) for b in db.scalars(select(Business).order_by(Business.position, Business.id))]


@router.post("/businesses")
def create_business(data: dict = Body(...), db=Depends(get_db)):
    biz = Business(name=data["name"], position=next_pos(db, Business))
    db.add(biz)
    db.commit()
    return row(biz)


@router.patch("/businesses/{id}")
def patch_business(id: int, data: dict = Body(...), db=Depends(get_db)):
    biz = apply(get_or_404(db, Business, id), data, ("name", "archived"))
    db.commit()
    return row(biz)


@router.delete("/businesses/{id}")
def delete_business(id: int, db=Depends(get_db)):
    """Удаляет бизнес вместе с его задачами, заметками и памятью."""
    db.execute(delete(Item).filter_by(list=f"biz:{id}:tasks"))
    db.execute(delete(Note).filter_by(list=f"biz:{id}"))
    db.execute(delete(Doc).filter_by(key=f"memory:biz:{id}"))
    db.execute(delete(Business).filter_by(id=id))
    db.commit()
    return {"ok": True}


# --- свои разделы ---

@router.get("/sections")
def list_sections(db=Depends(get_db)):
    return [row(s) for s in db.scalars(select(Section).order_by(Section.position, Section.id))]


@router.post("/sections")
def create_section(data: dict = Body(...), db=Depends(get_db)):
    section = Section(title=data["title"], tabs=[t for t in SECTION_TABS if t in data.get("tabs", [])],
                      position=next_pos(db, Section))
    db.add(section)
    db.commit()
    return row(section)


@router.patch("/sections/{id}")
def patch_section(id: int, data: dict = Body(...), db=Depends(get_db)):
    section = apply(get_or_404(db, Section, id), data, ("title",))
    db.commit()
    return row(section)


@router.delete("/sections/{id}")
def delete_section(id: int, db=Depends(get_db)):
    """Удаляет раздел со всеми его задачами, заметками, установками, планом, памятью и чатом."""
    key = f"s{id}"
    db.execute(delete(Item).where(Item.list.in_([f"{key}_tasks", f"{key}_mindsets"])))
    db.execute(delete(Note).filter_by(list=key))
    db.execute(delete(Doc).where(Doc.key.in_([f"memory:{key}", f"plan:{key}"])))
    db.execute(delete(Message).filter_by(chat=key))
    db.execute(delete(Section).filter_by(id=id))
    db.commit()
    return {"ok": True}


# --- expenses ---

@router.get("/expenses")
def list_expenses(kind: str, db=Depends(get_db)):
    return [row(e) for e in db.scalars(select(Expense).filter_by(kind=kind).order_by(Expense.id))]


@router.post("/expenses")
def create_expense(data: dict = Body(...), db=Depends(get_db)):
    exp = apply(Expense(), data, EXPENSE_FIELDS)
    db.add(exp)
    db.commit()
    return row(exp)


@router.patch("/expenses/{id}")
def patch_expense(id: int, data: dict = Body(...), db=Depends(get_db)):
    exp = apply(get_or_404(db, Expense, id), data, EXPENSE_FIELDS)
    db.commit()
    return row(exp)


@router.delete("/expenses/{id}")
def delete_expense(id: int, db=Depends(get_db)):
    db.execute(delete(Expense).filter_by(id=id))
    db.commit()
    return {"ok": True}


# --- accounts ---

@router.get("/accounts")
def list_accounts(db=Depends(get_db)):
    return accounts_view(db)


@router.post("/accounts")
def create_account(data: dict = Body(...), db=Depends(get_db)):
    acc = Account(name=data["name"])
    db.add(acc)
    db.flush()
    db.add(Balance(account_id=acc.id, amount=data.get("amount", 0)))
    db.commit()
    return {"ok": True}


@router.post("/accounts/{id}/balance")
def set_balance(id: int, data: dict = Body(...), db=Depends(get_db)):
    get_or_404(db, Account, id)
    db.add(Balance(account_id=id, amount=data["amount"]))
    db.commit()
    return {"ok": True}


@router.patch("/accounts/{id}")
def patch_account(id: int, data: dict = Body(...), db=Depends(get_db)):
    apply(get_or_404(db, Account, id), data, ("name", "archived"))
    db.commit()
    return {"ok": True}
