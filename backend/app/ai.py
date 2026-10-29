import datetime as dt
import json
import os
import threading
from zoneinfo import ZoneInfo

import openai
from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import delete, func, select

from .api import (EXPENSE_FIELDS, ITEM_FIELDS, NOTE_FIELDS, accounts_view, add_item, apply, items_query,
                  next_pos, rollover, row)
from .auth import require_auth
from .db import TZ, Session, get_db, now
from .models import Account, Balance, Business, Doc, Expense, Item, Message, Note, Reminder, Section

client = openai.OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY") or "not-set",
    http_client=openai.DefaultHttpx2Client(proxy=os.environ.get("OPENAI_PROXY") or None),
)
MODEL = os.environ.get("OPENAI_MODEL", "gpt-6.1-sol")
HISTORY = 80  # сколько последних сообщений диалога отправлять модели

CHATS = {
    "general": ("Общее", "Ты главный координатор. Помогаешь планировать день (задачи и блоки), разбирать мысли, "
                "отвечаешь на общие вопросы. У тебя доступ к данным и памяти всех разделов."),
    "economy": ("Экономика", "Ты личный экономический консультант: регулярные траты, подписки, где и сколько денег "
                "хранится. Помогаешь считать, планировать бюджет и оценивать идеи. Все суммы в рублях."),
    "admission": ("Поступление", "Ты помогаешь с поступлением: ведёшь задачи и заметки раздела, подсказываешь план."),
    "business": ("Бизнес", "Ты бизнес-консультант по всем бизнесам пользователя. Знаешь каждый бизнес (у каждого своя "
                 "память, задачи и заметки), обсуждаешь идеи, даёшь честные мнения и консультации."),
    "basketball": ("Баскетбол", "Ты тренер по баскетболу и менталити: материалы, мысли, установки, программа тренировок."),
    "cs2": ("CS2", "Ты помогаешь становиться сильнее в CS2: материалы, мысли о менталити, установки."),
    "gym": ("Зал", "Ты персональный S&C-тренер баскетболиста. Опирайся только на научно подтверждённые методы и практики "
            "профессиональных команд (NBA/NCAA), коротко объясняй «почему». Ведёшь тренировочный план в документе "
            "plan:gym: когда план на неделю меняется — переписывай документ целиком, сверху всегда текущая неделя. "
            "Каждую неделю уточняй дни практик и игры и раскладывай нагрузку по правилам из памяти. Думай долгосрочно: "
            "блоки, прогрессия, разгрузки, тесты. Рабочие веса, самочувствие, пропуски и итоги недель записывай в память "
            "(раздел «История»). Учитывай питание и восстановление — память раздела «Питание» можно прочитать через "
            "read_doc memory:food."),
    "food": ("Питание", "Ты спортивный нутрициолог. Опирайся на позиции ISSN и проверенные исследования, считай КБЖУ "
             "конкретно: граммы, ккал, белок. Ведёшь план питания в документе plan:food: при изменениях переписывай его "
             "целиком. Строго соблюдай ограничения и аллергии из памяти. План должен быть недорогим (Москва, дискаунтеры) "
             "и под готовку раз в неделю. Сверяй время приёмов пищи с расписанием тренировок (read_doc memory:gym, "
             "plan:gym). Вес, изменения нормы и итоги недель записывай в память."),
}

DATA_MAP = """## Данные приложения
Списки (items, поле list): day_tasks — задачи на день (с date), day_blocks — блоки/дела дня без времени (с date),
admission_tasks — задачи поступления, biz:<id>:tasks — задачи бизнеса, basketball_mindsets и cs2_mindsets —
установки (archived=true — в архиве). У задач done = выполнено.
Заметки (notes, поле list): general — заметки раздела «Общее», admission, biz:<id>, basketball_materials,
basketball_thoughts, cs2_materials, cs2_thoughts.
Документы (docs, по ключу): thoughts:YYYY-MM-DD — мысли за день, memory:<раздел> — твоя память раздела
(разделы: general, economy, admission, business, basketball, cs2, gym, food), memory:biz:<id> — память бизнеса,
plan:gym, plan:food — планы.
Экономика: expenses (kind=regular — регулярные траты, kind=subscription — подписки; период = every_n × unit,
unit: day|week|month), accounts — где хранятся деньги (баланс с историей).

## Правила
- Отвечай по-русски, коротко и по делу. Markdown можно.
- Всё, что нужно сделать с данными, делай инструментами сразу, не спрашивая разрешения.
- Важные долгосрочные факты о пользователе записывай в память раздела (write_doc с append=true, или перепиши
  память целиком, если её нужно навести в порядок). Не теряй старые факты при перезаписи.
- Напоминания ставь через add_reminder — они придут пушем на телефон."""


def doc_text(db, key):
    d = db.get(Doc, key)
    return d.text if d and d.text.strip() else "(пусто)"


TAB_DATA = {"tasks": "задачи — список {k}_tasks", "notes": "заметки — список {k}",
            "mindsets": "установки — список {k}_mindsets", "plan": "план — документ plan:{k}"}


def custom_section(db, chat):
    """Свой раздел по ключу чата s<id>, иначе None."""
    return db.get(Section, int(chat[1:])) if chat[:1] == "s" and chat[1:].isdigit() else None


def chat_info(db, chat):
    if chat in CHATS:
        return CHATS[chat]
    section = custom_section(db, chat)
    if not section:
        raise HTTPException(404)
    return section.title, (f"Ты помогаешь в разделе «{section.title}»: ведёшь его данные, отвечаешь на вопросы, "
                           "предлагаешь идеи. Подробности о разделе и о пользователе — в твоей памяти.")


def section_map(s):
    k = f"s{s.id}"
    data = [TAB_DATA[t].format(k=k) for t in s.tabs] + [f"память memory:{k}"]
    return f"- «{s.title}» (раздел {k}): " + ", ".join(data)


def system_prompt(db, chat):
    title, role = chat_info(db, chat)
    sections = db.scalars(select(Section).order_by(Section.position, Section.id)).all()
    parts = [f"Ты Альфред — личный ИИ-ассистент. Сейчас {now():%Y-%m-%d %H:%M, %A} ({TZ}).",
             f"Раздел: {title}. {role}", DATA_MAP]
    if sections:
        parts.append("## Свои разделы пользователя\n" + "\n".join(section_map(s) for s in sections))
    if chat == "general":
        memories = [(t, k) for k, (t, _) in CHATS.items()] + [(s.title, f"s{s.id}") for s in sections]
        parts += [f"## Память «{t}» (memory:{k})\n{doc_text(db, f'memory:{k}')}" for t, k in memories]
    else:
        parts.append(f"## Твоя память (memory:{chat})\n{doc_text(db, f'memory:{chat}')}")
    if chat in ("general", "business"):
        for b in db.scalars(select(Business).filter_by(archived=False).order_by(Business.position)):
            parts.append(f"## Бизнес «{b.name}» (id={b.id}), память memory:biz:{b.id}\n{doc_text(db, f'memory:biz:{b.id}')}")
    section = custom_section(db, chat)
    if chat in ("gym", "food") or (section and "plan" in section.tabs):
        parts.append(f"## Текущий план (plan:{chat})\n{doc_text(db, f'plan:{chat}')}")
    return "\n\n".join(parts)


# --- tools ---

def t_list_items(db, list, date=None):
    if list == "day_tasks":
        rollover(db)
    return [row(i) for i in db.scalars(items_query(list, date))]


def t_add_item(db, list, text, date=None):
    return row(add_item(db, list, text, date))


def t_update_item(db, id, **data):
    return row(apply(db.get(Item, id), data, ITEM_FIELDS))


def t_delete_item(db, id):
    db.execute(delete(Item).filter_by(id=id))
    return "ok"


def t_list_notes(db, list):
    return [{"id": n.id, "title": n.title, "updated_at": n.updated_at}
            for n in db.scalars(select(Note).filter_by(list=list).order_by(Note.updated_at.desc()))]


def t_read_note(db, id):
    return row(db.get(Note, id))


def t_save_note(db, title, body, id=None, list=None):
    note = db.get(Note, id) if id else Note(list=list)
    db.add(apply(note, {"title": title, "body": body}, NOTE_FIELDS))
    db.flush()
    return {"id": note.id}


def t_delete_note(db, id):
    db.execute(delete(Note).filter_by(id=id))
    return "ok"


def t_read_doc(db, key):
    d = db.get(Doc, key)
    return d.text if d else ""


def t_write_doc(db, key, text, append=False):
    d = db.get(Doc, key) or Doc(key=key, text="")
    d.text = (d.text.rstrip() + "\n" + text).strip() if append else text
    db.add(d)
    return "ok"


def t_list_docs(db, prefix):
    return [{"key": d.key, "text": d.text} for d in db.scalars(select(Doc).where(Doc.key.startswith(prefix)).order_by(Doc.key))]


def t_list_businesses(db):
    return [row(b) for b in db.scalars(select(Business).order_by(Business.position))]


def t_add_business(db, name):
    b = Business(name=name, position=next_pos(db, Business))
    db.add(b)
    db.flush()
    return row(b)


def t_list_expenses(db, kind=None):
    q = select(Expense).order_by(Expense.id)
    return [row(e) for e in db.scalars(q.filter_by(kind=kind) if kind else q)]


def t_save_expense(db, id=None, **data):
    e = db.get(Expense, id) if id else Expense()
    db.add(apply(e, data, EXPENSE_FIELDS))
    db.flush()
    return row(e)


def t_delete_expense(db, id):
    db.execute(delete(Expense).filter_by(id=id))
    return "ok"


def t_list_accounts(db):
    return accounts_view(db)


def t_add_account(db, name, amount):
    a = Account(name=name)
    db.add(a)
    db.flush()
    db.add(Balance(account_id=a.id, amount=amount))
    return {"id": a.id}


def t_set_balance(db, account_id, amount):
    db.add(Balance(account_id=account_id, amount=amount))
    return "ok"


def parse_time(s):
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=ZoneInfo(TZ))


def t_add_reminder(db, text, at):
    r = Reminder(text=text, at=parse_time(at))
    db.add(r)
    db.flush()
    return {"id": r.id}


def t_list_reminders(db):
    return [row(r) for r in db.scalars(select(Reminder).filter_by(sent=False).order_by(Reminder.at))]


def t_delete_reminder(db, id):
    db.execute(delete(Reminder).filter_by(id=id))
    return "ok"


S, I, B, N = {"type": "string"}, {"type": "integer"}, {"type": "boolean"}, {"type": "number"}
DATE = {"type": "string", "description": "YYYY-MM-DD"}
UNIT = {"type": "string", "enum": ["day", "week", "month"]}
KIND = {"type": "string", "enum": ["regular", "subscription"]}


def doc_label(key):
    for prefix, name in (("memory:", "память"), ("plan:", "план"), ("thoughts:", "мысли дня")):
        if key.startswith(prefix):
            return name
    return key


# name: (функция, описание, параметры, обязательные, подпись действия в чате или None для чтения)
TOOLS = {
    "list_items": (t_list_items, "Пункты списка", {"list": S, "date": DATE}, ["list"], None),
    "add_item": (t_add_item, "Добавить пункт в список", {"list": S, "text": S, "date": DATE}, ["list", "text"],
                 lambda a: f"добавил: {a['text']}"),
    "update_item": (t_update_item, "Изменить пункт", {"id": I, "text": S, "done": B, "archived": B, "date": DATE},
                    ["id"], lambda a: f"изменил: {a['text']}" if "text" in a else "обновил пункт"),
    "delete_item": (t_delete_item, "Удалить пункт", {"id": I}, ["id"], lambda a: "удалил пункт"),
    "list_notes": (t_list_notes, "Заметки списка (без текста)", {"list": S}, ["list"], None),
    "read_note": (t_read_note, "Прочитать заметку", {"id": I}, ["id"], None),
    "save_note": (t_save_note, "Создать (list) или перезаписать (id) заметку",
                  {"id": I, "list": S, "title": S, "body": S}, ["title", "body"],
                  lambda a: f"сохранил заметку «{a['title']}»"),
    "delete_note": (t_delete_note, "Удалить заметку", {"id": I}, ["id"], lambda a: "удалил заметку"),
    "read_doc": (t_read_doc, "Прочитать документ по ключу", {"key": S}, ["key"], None),
    "write_doc": (t_write_doc, "Записать документ (append=true — дописать в конец)",
                  {"key": S, "text": S, "append": B}, ["key", "text"], lambda a: f"обновил {doc_label(a['key'])}"),
    "list_docs": (t_list_docs, "Документы по префиксу ключа (например thoughts:2026-10)", {"prefix": S}, ["prefix"], None),
    "list_businesses": (t_list_businesses, "Список бизнесов", {}, [], None),
    "add_business": (t_add_business, "Добавить бизнес", {"name": S}, ["name"], lambda a: f"добавил бизнес {a['name']}"),
    "list_expenses": (t_list_expenses, "Регулярные траты и подписки", {"kind": KIND}, [], None),
    "save_expense": (t_save_expense, "Создать (без id) или изменить (id) трату/подписку",
                     {"id": I, "kind": KIND, "name": S, "amount": N, "every_n": I, "unit": UNIT, "note": S}, [],
                     lambda a: f"сохранил: {a.get('name', 'трату')}"),
    "delete_expense": (t_delete_expense, "Удалить трату/подписку", {"id": I}, ["id"], lambda a: "удалил трату"),
    "list_accounts": (t_list_accounts, "Где и сколько денег, с историей", {}, [], None),
    "add_account": (t_add_account, "Добавить место хранения денег", {"name": S, "amount": N}, ["name", "amount"],
                    lambda a: f"добавил счёт {a['name']}"),
    "set_balance": (t_set_balance, "Обновить сумму на счёте", {"account_id": I, "amount": N},
                    ["account_id", "amount"], lambda a: f"обновил баланс: {a['amount']} ₽"),
    "add_reminder": (t_add_reminder, "Поставить пуш-напоминание", {"text": S, "at": {"type": "string",
                     "description": "YYYY-MM-DDTHH:MM местного времени"}}, ["text", "at"],
                     lambda a: f"напомню {a['at'].replace('T', ' ')}: {a['text']}"),
    "list_reminders": (t_list_reminders, "Будущие напоминания", {}, [], None),
    "delete_reminder": (t_delete_reminder, "Отменить напоминание", {"id": I}, ["id"], lambda a: "отменил напоминание"),
}

TOOL_SCHEMAS = [{"type": "function", "name": name, "description": desc, "strict": False,
                 "parameters": {"type": "object", "properties": props, "required": req}}
                for name, (_, desc, props, req, _) in TOOLS.items()]


def run_tool(db, name, args_json):
    try:
        args = json.loads(args_json or "{}")
        fn, *_, label = TOOLS[name]
        result = fn(db, **args)
        db.commit()
        return json.dumps(jsonable_encoder(result), ensure_ascii=False), label(args) if label else None
    except Exception as e:
        db.rollback()
        return f"Ошибка: {e}", None


# --- история ---

def dialog(db, chat):
    last_reset = db.scalar(select(func.max(Message.id)).filter_by(chat=chat, role="reset")) or 0
    return db.scalars(select(Message).where(Message.chat == chat, Message.id > last_reset).order_by(Message.id)).all()


def to_input(m):
    """Сообщение из БД → элементы input для Responses API."""
    if m.role == "tool":
        return [{"type": "function_call_output", "call_id": m.meta["tool_call_id"], "output": m.content}]
    items = [{"role": m.role, "content": m.content}] if m.content else []
    for c in (m.meta or {}).get("tool_calls", []):
        items.append({"type": "function_call", "call_id": c["id"], "name": c["function"]["name"],
                      "arguments": c["function"]["arguments"]})
    return items


def context(db, chat):
    msgs = dialog(db, chat)[-HISTORY:]
    while msgs and msgs[0].role != "user":
        msgs = msgs[1:]
    return [item for m in msgs for item in to_input(m)]


router = APIRouter(prefix="/api/chat", dependencies=[Depends(require_auth)])

# Ответ ИИ считается в фоновом потоке, поэтому не обрывается, если закрыть приложение.
# running — чаты, где ответ ещё готовится; errors — ошибка последнего ответа (отдаётся один раз).
running: set[str] = set()
errors: dict[str, str] = {}
lock = threading.Lock()


@router.get("/{chat}")
def history(chat: str, db=Depends(get_db)):
    chat_info(db, chat)
    return {"messages": [row(m) for m in dialog(db, chat)], "busy": chat in running, "error": errors.pop(chat, None)}


@router.post("/{chat}/reset")
def reset(chat: str, db=Depends(get_db)):
    chat_info(db, chat)
    db.add(Message(chat=chat, role="reset"))
    db.commit()
    return {"ok": True}


@router.post("/{chat}")
def send(chat: str, data: dict = Body(...), db=Depends(get_db)):
    chat_info(db, chat)
    with lock:
        if chat in running:
            raise HTTPException(409, "Альфред ещё отвечает на прошлое сообщение")
        running.add(chat)
    try:
        db.add(Message(chat=chat, role="user", content=data["text"]))
        db.commit()
    except Exception:
        running.discard(chat)
        raise
    threading.Thread(target=respond, args=(chat,), daemon=True).start()
    return {"ok": True}


def respond(chat):
    try:
        with Session() as db:
            answer(db, chat)
    except Exception as e:
        errors[chat] = f"Ошибка: {e}"
    finally:
        running.discard(chat)


def answer(db, chat):
    # первый запрос — вся история; дальше результаты инструментов цепляются через previous_response_id,
    # чтобы модель сохраняла рассуждения между вызовами
    request = {"input": context(db, chat)}
    for _ in range(10):
        r = client.responses.create(model=MODEL, tools=TOOL_SCHEMAS, instructions=system_prompt(db, chat), **request)
        calls = [{"id": o.call_id, "type": "function", "function": {"name": o.name, "arguments": o.arguments}}
                 for o in r.output if o.type == "function_call"]
        batch = [Message(chat=chat, role="assistant", content=r.output_text or "", meta={"tool_calls": calls} if calls else None)]
        for c in calls:
            result, label = run_tool(db, c["function"]["name"], c["function"]["arguments"])
            batch.append(Message(chat=chat, role="tool", content=result, meta={"tool_call_id": c["id"], "label": label}))
        db.add_all(batch)
        db.commit()
        if not calls:
            break
        request = {"previous_response_id": r.id, "input": [i for m in batch[1:] for i in to_input(m)]}
