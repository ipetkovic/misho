# AGENTS.md

Guidance for AI coding agents working in this repository.

## What this is

Misho automates court reservations on `sportbooking.info` (a Croatian tennis club booking site with no public API).
Users talk to a Telegram bot in Croatian; an OpenAI function-calling layer turns their messages into *jobs*, and
background cron tasks race to grab courts the moment they become bookable.

## Commands

All commands run from the **repo root** — `alembic.ini` and `CONFIG.database_path` both use the relative path
`db/sportbooking.db`, so running elsewhere silently creates/uses a different database.

```bash
uv sync --all-packages         # a bare `uv sync` installs ONLY the root tooling deps,
                               # which leaves pyright unable to resolve the app's imports
source .env                    # see .env.example; MISHO_ENVIRONMENT must be TEST or PROD
uv run misho-server            # run the whole app (migrations + schedulers + bot)
uv run pyright                 # type check — [tool.pyright] in pyproject.toml pins basic mode
```

Migrations (Alembic, models in `infrastructure/persistance/model.py`):

```bash
uv run alembic -c misho-server/src/misho_server/alembic.ini revision --autogenerate -m "msg"
uv run alembic -c misho-server/src/misho_server/alembic.ini upgrade head
```

`migrate()` runs automatically on startup and also seeds `hour_slots` and `courts` (ids 4–8) — seed data lives in
`infrastructure/persistance/migration.py`, not in a migration.

Deploy — **pushing to `main` deploys**. There is no manual deploy script; `build.py` and `deploy.py`
were deleted along with the paramiko/scp dependencies.

```bash
docker compose up --build                  # local container run; override.yml builds from source
curl -s localhost:8000/healthz             # scheduler + Telegram polling + SQLite

gh workflow run deploy.yml -f tag=<sha>    # redeploy or roll forward an existing image by hand
gcloud compute ssh misho --project <project> --zone <zone> --tunnel-through-iap  # debug (then `sudo docker ...`)
terraform -chdir=terraform apply           # provision; see README for the two-phase first run
```

`.github/workflows/deploy.yml` type-checks, builds `linux/amd64` **without pushing**, smoke-tests
that image (Alembic migrations in a throwaway container + the PROD config loading), and only then
publishes `ghcr.io/ipetkovic/misho:<sha>`. It authenticates to GCP by OIDC — Workload Identity
Federation, no stored key — and reaches the VM through an IAP tunnel; port 22 is closed to the
internet. `deploy/remote-deploy.sh` then does the swap on the VM and **restores the previous tag if
`/healthz` never goes healthy**, keeping the last three images locally so a rollback needs no network.

Not a rolling update: the bot long-polls Telegram, so two live containers would fight over
`getUpdates` (409) and run two schedulers racing for the same court.

On the VM the app lives in `/opt/misho`, where `./db` is a separately-managed persistent disk — the
SQLite file survives instance replacement but not `terraform destroy`. **`/opt/misho/.env` does not**:
it is on the boot disk and is re-rendered from GitHub secrets on every deploy, so a replaced instance
stays down until a deploy runs.

There is no test suite. The CI smoke test is the only automated check that the app can start.

## Workspace layout

uv workspace with two members:

- **`sportbooking/`** — standalone async client for `sportbooking.info`. Pure HTTP + HTML scraping (httpx + bs4/lxml),
  knows nothing about Misho. Public modules re-export pydantic models; everything under `_internal/` is private.
  A "session token" is the raw `Set-Cookie` string; success/failure is detected by grepping for marker strings in the
  HTML body (e.g. login checks for `window.location.replace('main/clan.php')`), so site markup changes break it silently.
- **`misho-server/`** — the application. Entry point `misho_server:main`.

Root `pyproject.toml` holds only the workspace definition and the pyright config/dependency.

## misho-server architecture

Four layers under `misho-server/src/misho_server/`:

- **`core/`** — domain models (frozen pydantic) and *abstract repository interfaces*. No I/O, no framework imports.
  Interfaces are plain classes whose methods `raise NotImplementedError()` — not ABCs or Protocols; follow that style.
  Each concept is a package: `core/job/__init__.py` holds `Job`, `core/job/jobs_repository.py` holds `JobsRepository`.
- **`service/`** — orchestration. Services depend only on `core` interfaces and other services.
- **`infrastructure/persistance/`** — SQLAlchemy async (aiosqlite) implementations, named `<Thing>RepositorySqlite`.
  Each module exports a module-level `to_domain(dao) -> domain` function that other repositories import and reuse
  (e.g. `jobs_repository` imports `time_slot_repository.to_domain`). `model.py` is the ORM layer, imported as `dao`.
- **`interfaces/`** — inbound adapters: `telegram_bot/`, `open_ai/`, and `health/` (the only real
  inbound HTTP surface — `GET /healthz`, read by the Docker `HEALTHCHECK`, the autoheal sidecar and
  the deploy rollout; never exposed through the firewall).

**`__init__.py:start()` is the single composition root.** Every repository, service and adapter is constructed and
wired by hand there, and the APScheduler jobs are registered there. Anything new must be added to that function —
there is no DI container.

`start()` ends by awaiting a `SIGTERM`/`SIGINT` event, not by sleeping forever, and tears down the
health server and scheduler in a `finally`. The Dockerfile's `CMD` is exec-form so Python is PID 1 and
actually receives the signal — under the old `uv run` form the signal reached `uv`, nothing unwound,
and Docker SIGKILLed after the full 10s grace period, abandoning in-flight reservations. Anything
long-running added to `start()` belongs in that teardown.

### The reservation flow

1. A user asks the bot for a slot → `JobsService.create_job` stores a `Job` (`action` = `RESERVE` or `NOTIFY`) with a
   `TimeSlot` and `courts_by_priority`. Jobs reference pre-existing `time_slots` rows; startup pre-populates 100 days
   of them (`insert_time_slots`), so a job outside that window cannot be created.
2. `ReservationMonitoring` (cron, every 10s in dev) asks
   `AvailableJobReservationSlotRepository` for the join of active RESERVE jobs × courts currently free in the synced
   calendar. At midnight it instead fires `_handle_new_day` for `today + 4` — the day the site newly opens for booking.
3. `ReservationSchedulerImpl` groups jobs by `TimeSlot` and builds one **shared court pool per time slot**;
   `ReserveJobExecutor` walks `courts_by_priority` and *removes* a court from that pool before attempting it, so two
   jobs in the same slot never fight over the same court.
4. Success/failure is pushed through `NotificationService` (in-process subscriber list; `TelegramBotImpl` subscribes).

Supporting cron tasks, all with `CronTrigger`s defined in `config/`: `reservation_calendar_sync` (refresh the shared
calendar), `job_expired_handler` (delete expired jobs, optionally spawn a follow-up NOTIFY job via `OnExpiryAction`),
`job_notifier` (edge-triggered "court freed / court taken" messages), `reservation_notification_service`
(reminders N minutes before a booked slot).

### Cross-cutting pieces

- **`ReservationUpdateBus`** — in-process async pub/sub. `ReservationService`/`ReservationCancelService` publish after a
  successful mutation; `ReservationCalendarSyncService` subscribes and re-syncs immediately instead of waiting for cron.
- **Two calendar types.** `UserReservationCalendar` is per-user and carries the reserve/cancel links (only obtainable
  with that user's session token); `ReservationCalendar` is the stripped, shared, persisted view (`reserved_by` only)
  that monitoring queries against. `ReservationCalendar.from_user_reservation_calendar` converts between them.
- **`SessionTokenFetchService`** caches a sportbooking session cookie per user and re-logs in after 20 minutes.
- **Config**: `MISHO_ENVIRONMENT` selects `config/test.py` or `config/prod.py` and **raises on anything
  else** — it used to fall back to dev silently, which meant a typo ran test settings in production.
  `dummy_reservation` skips the actual HTTP reserve/cancel call and is `True` in TEST, so local runs
  cannot book a real court; it is `False` in PROD.

### Telegram + OpenAI layer

`TelegramHandlerDelegator` routes every update to one of three handlers based on DB state: no
`user_telegram_notifications` row → **blacklisted** (silently ignored); rows are created by `TelegramInviteService`,
either by the `/invite` command or by the startup seed of `MISHO_ADMIN_TELEGRAM_USERNAME`;
row without `user_id` → **onboarding** (`/signup <user> <pass>`, verified against sportbooking); otherwise **standard**.
`/invite` is the exception to that routing: it is gated on *who* sends it rather than on their state, so
`TelegramAdminHandler` is registered straight onto `TelegramBotImpl` and never passes through the delegator.

The standard handler holds one `OpenAiUserClient` per Telegram username: a `gpt-4o` chat loop with hand-written tool
schemas in `interfaces/open_ai/tools.py`, dispatched by function-name string in `tool_handler.py`, with conversation
context cleared after 10 minutes of inactivity. Tool errors are caught and returned to the model as strings rather
than raised. Notifications are injected into that conversation as `system` messages so the model stays consistent
with what the user was just told.

## Conventions

- All user-facing text (Telegram messages, notification bodies, the OpenAI system prompt) is **Croatian**;
  code, logs and identifiers are English.
- Domain models are `pydantic.BaseModel` with `model_config = ConfigDict(extra='ignore', frozen=True)` — frozen matters
  because `TimeSlot`/`ReservationSlot` are used as dict keys throughout.
- `type X = int` aliases (`JobId`, `UserId`, `CourtId`, `ChatId`) live next to the model they identify.
- Evening hour slots are 2 hours long (17–19, 19–21, 21–23), the rest are 1 hour; the OpenAI tool descriptions encode
  this rule for the model.

## Known rough edges

- `core/job_notification.py` and `core/job_notification/__init__.py` both exist with identical content. The package
  wins on import, so the flat module is dead code — delete it rather than editing it.
- `print()` calls are scattered through repositories and services alongside `logging`.
