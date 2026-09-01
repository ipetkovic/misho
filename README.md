# Misho

A Telegram bot that books tennis courts on [sportbooking.info](https://sportbooking.info), a club
reservation site with no public API. You tell the bot — in Croatian — which slot you want; it creates a
*job* and then races to claim the court the moment it becomes bookable, whether that's at midnight when
a new day opens or the second somebody else cancels.

Personal project, so it's wired to one club's courts and speaks Croatian. Public because there's no
reason for it not to be.

## How it works

The site opens reservations roughly four days ahead, which makes booking a popular evening slot a race.
Misho automates the race:

- **New day.** At midnight, `ReservationMonitoring._handle_new_day` fires for `today + 4` and
  immediately attempts every reservation job scheduled for that date.
- **Cancellations.** Between those windows it re-checks every 10–30 seconds, so a slot freed by
  somebody else's cancellation gets picked up rather than sitting there.
- **Two kinds of job.** `RESERVE` claims the court. `NOTIFY` just messages you when it frees up. A
  `RESERVE` job that expires without succeeding can turn itself into a `NOTIFY` job via
  `OnExpiryAction.CREATE_NOTIFY_JOB`.
- **Court pools.** `ReservationSchedulerImpl` builds one shared pool of courts per time slot and each
  job removes a court from it before attempting, so two of your own jobs never compete for the same court.

Conversation with the bot goes through OpenAI function calling — `gpt-4o` with hand-written tool schemas
that map "rezerviraj mi teren u petak u 19h" onto `create_job`, `reserve`, `get_reservations` and friends.

## Stack

Python 3.12 · [uv](https://docs.astral.sh/uv/) workspace · SQLAlchemy (async) + aiosqlite · Alembic ·
APScheduler · python-telegram-bot · httpx + BeautifulSoup/lxml · OpenAI `gpt-4o`

Two workspace members:

| | |
|---|---|
| `sportbooking/` | Standalone async client for sportbooking.info. Pure HTTP and HTML scraping; knows nothing about Misho. |
| `misho-server/` | The application — domain, services, persistence, and the Telegram/OpenAI adapters. |

## Running locally

Everything runs **from the repository root**. Both `alembic.ini` and `CONFIG.database_path` use the
relative path `db/sportbooking.db`, so running from elsewhere silently uses a different database.

```bash
uv sync
mkdir -p db          # gitignored, and SQLite won't create the directory itself
source .env
uv run misho-server
```

Startup runs the migrations, seeds reference data, starts the schedulers, and begins polling Telegram.

Three environment variables matter:

| Variable | |
|---|---|
| `MISHO_ENVIRONMENT` | `DEV` or `PROD` — selects `config/dev.py` or `config/prod.py`. Anything else falls back to dev. |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/botfather). |
| `OPENAI_API_KEY` | Read implicitly by the OpenAI SDK. |

While developing against the live site, set `dummy_reservation = True` in the active config. Everything
runs normally except the final reserve/cancel HTTP call, so you can exercise the whole flow without
actually booking a court.

Type checking (the project is written for pyright strict):

```bash
uv run pyright
```

## Granting someone access

The bot ignores anyone it doesn't already know — `TelegramHandlerDelegator` treats an unrecognised
Telegram username as blacklisted and silently drops the message. There's deliberately no self-serve
path: an open bot would let any stranger spend your OpenAI budget and book real courts. So onboarding
somebody is two steps.

**1. Invite their Telegram username**, from inside Telegram:

```
/invite their_telegram_username
```

Only `MISHO_ADMIN_TELEGRAM_USERNAME` may run this; for anyone else the command stays silent, exactly
like the blacklist. The username has to match the casing Telegram reports, and a leading `@` is
stripped for you.

That admin row is itself seeded on every startup, so the deployer is never locked out of their own
bot. Leave the variable unset and `/invite` is disabled — the allow-list then has to be seeded by
hand, remembering that `enable_notifications`, `created_at` and `updated_at` are `NOT NULL` without
database-level defaults:

```sql
INSERT INTO user_telegram_notifications
  (username, enable_notifications, created_at, updated_at)
VALUES ('their_telegram_username', 1, datetime('now'), datetime('now'));
```

**2. They link their sportbooking account** by messaging the bot:

```
/signup <sportbooking-username> <sportbooking-password>
```

Misho verifies the credentials against the site, reads their display name from it, and links the
accounts. Quote any value containing spaces: `/signup "korisničko ime" "lozinka"`.

`/start` is optional — `chat_id`, which every outbound notification needs, is refreshed from any
update the user sends, so signing up is enough to start receiving them.

## Deployment

The bot runs as a single container on a GCP `e2-micro`, provisioned by `terraform/`. It makes only
outbound connections — Telegram long polling, OpenAI, sportbooking.info — so nothing listens and SSH is
the only open port.

### Cost

Instance hours and 30 GB of `pd-standard` fall under the GCP free tier. **The external IPv4 does not** —
it bills at ~$0.005/hour, about **$3.65/month**. That's still the cheapest workable option: Cloud NAT
runs ~$32/month, and an IPv6-only VM can't reach sportbooking.info, which has no AAAA record.

Free tier requires all of:

- Region `us-west1`, `us-central1` or `us-east1` — enforced by a variable validation in `terraform/variables.tf`
- Machine type `e2-micro`, one instance
- `pd-standard` disks totalling ≤ 30 GB (defaults here: 20 GB boot + 10 GB data)

### First run

```bash
gcloud auth application-default login

cd terraform
cp terraform.tfvars.example terraform.tfvars   # set project_id; narrow ssh_source_ranges
terraform init
terraform apply
```

`ssh_source_ranges` defaults to `0.0.0.0/0`. Narrow it to your own address.

### Build and ship

```bash
uv run ./build.py --push -t mojo28/misho:latest
export MISHO_HOST=$(terraform -chdir=terraform output -raw external_ip)
uv run ./deploy.py ~/.ssh/id_ed25519 --username misho
```

> **Set `MISHO_ENVIRONMENT=PROD` in `.env` first.** `deploy.py` copies `.env` to the server verbatim,
> and the local value is `DEV` — deploy as-is and the VM gets debug logging and a 10-second monitoring
> cron instead of 30.

`deploy.py` copies `docker-compose.yml` and `.env` into `/opt/misho` and runs `docker compose up -d`
there, so the compose file's relative `./db` volume lands on the mounted data disk.

### What Terraform sets up

- **A separate data disk.** `misho-data` is its own `google_compute_disk`, so replacing the instance —
  image bump, machine type change, startup-script edit — leaves the database untouched. `terraform
  destroy` *will* delete it; add `lifecycle { prevent_destroy = true }` to that resource if you'd
  rather it fail loudly.
- **`startup.sh`, on every boot**, idempotently: formats the data disk on first boot only, adds 1 GB of
  swap (the e2-micro has 1 GB of RAM), installs Docker, and creates `/opt/misho` owned by the deploy user.
- **Minimal networking.** A dedicated VPC and subnet, plus one firewall rule for SSH.

### Timezone

The host stays on UTC. `TZ=Europe/Berlin` is set on the *container* in `docker-compose.yml`, and that's
the one that matters — the midnight new-day branch in `ReservationMonitoring` reads `datetime.now()`
inside the container.

### Logs

Container stdout goes to Cloud Logging via Docker's `gcplogs` driver, applied by the
server-only `docker-compose.gcp.yml` overlay. No Ops Agent, so nothing extra competes
for the 1 GB of RAM.

```bash
# application logs
gcloud logging read 'logName:"gcplogs-docker-driver"' \
  --project=misho-bot-4821 --limit=50 --freshness=1h \
  --format="value(timestamp,jsonPayload.message)"

# boot / provisioning, shipped by the built-in guest agent
gcloud logging read 'logName:"google_metadata_script_runner"' \
  --project=misho-bot-4821 --limit=50 --freshness=1h --format="value(textPayload)"
```

Docker's dual-logging cache keeps `docker logs` working too, so the SSH route is still
available and is the quickest way to tail:

```bash
ssh misho@$MISHO_HOST 'cd /opt/misho && docker compose logs -f'
```

### Backups

`/opt/misho/db/sportbooking.db` is the only state, and it holds every linked account and pending job:

```bash
scp misho@$MISHO_HOST:/opt/misho/db/sportbooking.db ./backup.db
```

## Database

Alembic migrations; models live in `misho-server/src/misho_server/infrastructure/persistance/model.py`.

```bash
uv run alembic -c misho-server/src/misho_server/alembic.ini revision --autogenerate -m "msg"
uv run alembic -c misho-server/src/misho_server/alembic.ini upgrade head
```

`migrate()` runs automatically at startup. It also seeds the `hour_slots` and `courts` tables (court ids
4–8) — that seed data lives in `infrastructure/persistance/migration.py`, not in a migration. Evening
slots are two hours long (17–19, 19–21, 21–23); the rest are one.

## Repository layout

| Path | |
|---|---|
| `misho-server/` | The application |
| `sportbooking/` | Standalone sportbooking.info client |
| `terraform/` | GCP provisioning |
| `build.py` | Builds and pushes the Docker image |
| `deploy.py` | Ships compose file + `.env` to the VM and restarts it |
| `AGENTS.md` | Architecture notes for coding agents — layering, conventions, how the pieces connect |

## License

MIT © 2025 Ivo Petković
