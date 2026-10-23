# Alfred

Личное PWA для организации жизни с ИИ. FastAPI + Postgres + Vue, всё в Docker.
Работает на `alfred.bbifather.site` рядом с bbifather, за уже установленным на сервере nginx.

## 1. Поддомен

В панели регистратора домена `bbifather.site` → DNS-записи → добавить:

| Тип | Имя | Значение |
|-----|-----|----------|
| A | `alfred` | IP сервера (тот же, что у записи `@` для bbifather.site) |

Если у bbifather есть AAAA-запись (IPv6) — добавь такую же AAAA для `alfred`.
Подожди 5–30 минут и проверь с мака: `dig +short alfred.bbifather.site` — должен вернуть IP сервера.

## 2. Запуск на сервере

```bash
cd <папка, где лежит bbifather>/..
git clone <repo> alfred && cd alfred
cp .env.example .env
./alfred.sh vapid          # выведет VAPID_PUBLIC_KEY и VAPID_PRIVATE_KEY — вставь их в .env
nano .env                  # PIN, пароль БД, ключ OpenAI, прокси
./alfred.sh up
```

Если порт 8100 на сервере занят — поменяй `PORT` в `.env` и в `deploy/nginx-alfred.conf`.

### Стартовая память (папка `seed/`, в git не попадает)

Файлы `seed/*.md` при старте загружаются в документы приложения: имя файла → ключ документа
(`memory.gym.md` → `memory:gym`, `plan.food.md` → `plan:food`, `memory.biz.1.md` → `memory:biz:1`).
Загружается только в пустой документ — то, что уже изменено в приложении, не перезаписывается.
Репозиторий публичный, поэтому папку копируй на сервер вручную, с мака:

```bash
scp -r seed user@сервер:<путь>/alfred/ && ssh user@сервер "cd <путь>/alfred && ./alfred.sh up"
```

## 3. nginx + HTTPS

```bash
sudo cp deploy/nginx-alfred.conf /etc/nginx/sites-available/alfred
sudo ln -s /etc/nginx/sites-available/alfred /etc/nginx/sites-enabled/alfred
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d alfred.bbifather.site
```

Конфиг bbifather не трогается. certbot сам добавит HTTPS и редирект с http.
Проверка: `curl -I https://alfred.bbifather.site` → `200` и `X-Robots-Tag: noindex, nofollow`.

## 4. iPhone

1. Safari → `alfred.bbifather.site` → «Поделиться» → «На экран Домой».
2. Открыть Alfred с иконки → ввести PIN.
3. ☰ → Настройки → включить Face ID и уведомления (только из приложения с экрана «Домой», iOS 16.4+).
4. В «Зал» и «Питание» → «Память» — вставь экспорт из старых чатов с Claude.

## Команды

```bash
./alfred.sh up      # git pull + сборка + перезапуск (и первый запуск, и обновление)
./alfred.sh logs    # логи приложения
./alfred.sh down    # остановить
./alfred.sh vapid   # сгенерировать ключи для пушей
```

Обновление: `git push` с мака → на сервере `./alfred.sh up`.

## Как устроено

- `backend/app` — FastAPI: `api.py` (данные), `ai.py` (чаты и инструменты ИИ), `auth.py` (PIN + Face ID),
  `push.py` (пуш-напоминания), `models.py` (таблицы). Таблицы создаются автоматически при старте.
- `frontend/src` — Vue: `views/` — экраны разделов, `components/` — списки, заметки, документы.
- В каждом разделе есть чат. ИИ видит память своего раздела, может читать и менять все данные,
  дополнять свою память и ставить напоминания. «Новый» в чате очищает контекст, история остаётся в базе.
- Блокировка: после 3 минут в фоне — Face ID, при отмене — PIN.
