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
uv sync --all-packages     # a bare `uv sync` installs only the root tooling deps
cp .env.example .env       # then fill it in
mkdir -p db                # gitignored, and SQLite won't create the directory itself
source .env
uv run misho-server
```

Or in a container, which is what production runs — `docker-compose.override.yml` is loaded
automatically and builds from source:

```bash
docker compose up --build
curl -s localhost:8000/healthz | jq
```

Startup runs the migrations, seeds reference data, starts the schedulers, and begins polling Telegram.

Four environment variables matter:

| Variable | |
|---|---|
| `MISHO_ENVIRONMENT` | `TEST` or `PROD`, selecting `config/test.py` or `config/prod.py`. **Anything else is a fatal startup error** — it used to fall back to the dev config silently, so a typo ran test settings against the live site. |
| `TELEGRAM_BOT_TOKEN` | From [@BotFather](https://t.me/botfather). |
| `OPENAI_API_KEY` | Read implicitly by the OpenAI SDK. |
| `MISHO_ADMIN_TELEGRAM_USERNAME` | Allow-listed on startup; the only user who may run `/invite`. |

> **Use a second BotFather bot locally.** Telegram delivers each update exactly once per token, so a
> local instance sharing the production token silently steals real users' messages.

`TEST` sets `dummy_reservation=True`: everything runs normally except the final reserve/cancel HTTP
call, so the whole flow is exercisable without booking a real court. `PROD` books for real.

Type checking:

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
outbound connections — Telegram long polling, OpenAI, sportbooking.info — so nothing listens
publicly. SSH arrives through an IAP tunnel; port 22 is closed to the internet.

Pushing to `main` builds, verifies and rolls out automatically
(`.github/workflows/deploy.yml`). There is no manual deploy script.

### Cost

Instance hours and 30 GB of `pd-standard` fall under the GCP free tier. **The external IPv4 does not** —
it bills at ~$0.005/hour, about **$3.65/month**. That's still the cheapest workable option: Cloud NAT
runs ~$32/month, and an IPv6-only VM can't reach sportbooking.info, which has no AAAA record.

Free tier requires all of:

- Region `us-west1`, `us-central1` or `us-east1` — enforced by a variable validation in `terraform/variables.tf`
- Machine type `e2-micro`, one instance
- `pd-standard` disks totalling ≤ 30 GB (defaults here: 20 GB boot + 10 GB data)

`ghcr.io` is free for public packages, with no storage or bandwidth quota.

### First run

Apply in two phases. The single apply enables OS Login *and* closes public SSH at the same time, so
if the OS Login grants are wrong you lose both ways in at once.

```bash
gcloud auth application-default login

cd terraform
cp terraform.tfvars.example terraform.tfvars   # set project_id

# Phase 1 — build the IAP/OS Login/WIF machinery, keeping the old way in.
terraform init
terraform apply -var='ssh_source_ranges=["0.0.0.0/0"]'

# Verify the tunnel works BEFORE giving up the public route.
# --project is not optional: without it gcloud uses whatever `gcloud config
# get-value project` returns, and a 404 for instance "misho" in some other
# project is the confusing result.
gcloud compute ssh misho --project misho-bot-4821 --zone us-central1-a --tunnel-through-iap

# Phase 2 — close port 22 to the internet (ssh_source_ranges defaults to []).
terraform apply
```

> **`terraform destroy` leaves the Workload Identity Pool behind.** It is soft-deleted for 30 days
> with its ID reserved, so a later apply fails with `Error 409: Requested entity already exists`.
> Undelete it and import it rather than renaming anything:
>
> ```bash
> gcloud iam workload-identity-pools undelete github --location=global
> terraform -chdir=terraform import google_iam_workload_identity_pool.github \
>   projects/$PROJECT/locations/global/workloadIdentityPools/github
> ```
>
> Check `gcloud iam workload-identity-pools providers list --workload-identity-pool=github
> --location=global` too; if the provider also came back `DELETED`, undelete and import it the same
> way. Service accounts, by contrast, recreate cleanly under the same ID.

If phase 1's SSH check fails, grant yourself OS Login with sudo and retry:

```bash
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="user:$(gcloud config get-value account)" --role=roles/compute.osAdminLogin
```

### Wiring up GitHub

`terraform output github_actions_variables` prints everything the workflow needs. Under
**Settings → Secrets and variables → Actions**:

*Variables* (identifiers, not secrets — Workload Identity Federation grants nothing without a signed
OIDC token whose `repository` claim matches):

| Variable | Source |
| --- | --- |
| `GCP_PROJECT_ID` | `terraform output` |
| `GCP_ZONE` | `terraform output` |
| `GCP_INSTANCE` | `terraform output` |
| `GCP_WIF_PROVIDER` | `terraform output` |
| `GCP_DEPLOY_SA` | `terraform output` |

*Secrets*: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, `MISHO_ADMIN_TELEGRAM_USERNAME`.

`MISHO_ENVIRONMENT=PROD` is written by the workflow itself, not stored.

> **After the first successful push, set the package to public.** A new `ghcr.io` package is private
> even when the repository is public, and the VM pulls anonymously — so the first rollout fails with
> `unauthorized` until you change it. Go to the repository's **Packages** → `misho` → **Package
> settings** → **Change visibility** → Public. Public packages have no storage or bandwidth quota;
> private ones would need a long-lived pull token on the VM, defeating the point of OIDC.

> Secrets live only in GitHub, so a Terraform-replaced instance comes up with an empty
> `TELEGRAM_BOT_TOKEN` and fails its healthcheck until a deploy re-runs. `/opt/misho` sits on the
> boot disk; only `/opt/misho/db` is the persistent one.

### How a deploy works

`.github/workflows/deploy.yml`, on push to `main` or `workflow_dispatch`:

1. `uv run pyright`.
2. Build `linux/amd64` and **load without pushing**.
3. Smoke-test that image: run Alembic migrations in a throwaway container, and check the PROD config
   loads. There is no test suite, so this is the only gate on the app being able to start — and
   nothing is published until it passes.
4. Push `ghcr.io/ipetkovic/misho:<sha>` and `:latest`.
5. Authenticate to GCP by OIDC, render `.env` from secrets, and stage it with the compose files onto
   the VM through the IAP tunnel.
6. Run `deploy/remote-deploy.sh`, which pulls, restarts, and **polls `/healthz` until healthy —
   restoring the previous tag if it never gets there.** The last three images are kept on the VM, so
   a rollback needs no network.

This is not a rolling update. The bot consumes Telegram updates by long polling, so two live
containers would fight over `getUpdates` (HTTP 409) and run two reservation schedulers racing for the
same court. The swap is stop-then-start, costing a few seconds of downtime.

Redeploy an existing tag, or roll forward by hand:

```bash
gh workflow run deploy.yml -f tag=<sha>
```

### Health and self-healing

The container serves `GET /healthz` on port 8000, asserting that the APScheduler is running, the
Telegram updater is polling, and SQLite answers `SELECT 1`. It is never published through the
firewall — the Docker `HEALTHCHECK` and the rollout script both probe it from inside.

`restart: unless-stopped` only reacts to the process *exiting*, and Docker does not act on an
unhealthy status by itself. The `autoheal` sidecar in `docker-compose.gcp.yml` watches the health
status and restarts the container. It is deliberately a separate container: an in-process supervisor
cannot rescue a blocked event loop, which is exactly the failure that leaves the process up while the
bot has gone deaf.

### Debugging on the VM

```bash
gcloud compute ssh misho --project misho-bot-4821 --zone us-central1-a --tunnel-through-iap

sudo docker ps
sudo docker inspect -f '{{json .State.Health}}' misho
sudo docker logs --tail 100 misho
sudo cat /opt/misho/.env | grep MISHO_IMAGE_TAG   # which build is live
```

Container logs also go to Cloud Logging via the `gcplogs` driver.

Back up the database:

```bash
gcloud compute scp misho:/opt/misho/db/sportbooking.db ./backup.db \
  --project misho-bot-4821 --zone us-central1-a --tunnel-through-iap
```

### What Terraform sets up

- **A separate data disk.** `misho-data` is its own `google_compute_disk`, so replacing the instance —
  image bump, machine type change, startup-script edit — leaves the database untouched. `terraform
  destroy` *will* delete it; add `lifecycle { prevent_destroy = true }` to that resource if you'd
  rather it fail loudly.
- **`startup.sh`, on every boot**, idempotently: formats the data disk on first boot only, adds 1 GB of
  swap (the e2-micro has 1 GB of RAM), installs Docker, and creates `/opt/misho` owned by the deploy user.
- **Minimal networking.** A dedicated VPC and subnet, with SSH reachable only from IAP's
  `35.235.240.0/20`. The direct-SSH rule exists but is created only when `ssh_source_ranges` is
  non-empty, which it is not by default.
- **Workload Identity Federation** (`terraform/github.tf`) so GitHub Actions authenticates with a
  short-lived OIDC token instead of a stored key, restricted by an attribute condition to this
  repository. The deployer gets `iap.tunnelResourceAccessor`, `compute.viewer` and
  `compute.osAdminLogin` — the last because an OS Login service account logs in as
  `sa_<numeric-uid>`, which is not the `misho` user, is not in the `docker` group, and needs sudo to
  write to `/opt/misho`.

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
gcloud compute ssh misho --project misho-bot-4821 --zone us-central1-a \
  --tunnel-through-iap --command 'sudo docker logs -f misho'
```

### Backups

`/opt/misho/db/sportbooking.db` is the only state, and it holds every linked account and pending job:

```bash
gcloud compute scp misho:/opt/misho/db/sportbooking.db ./backup.db \
  --project misho-bot-4821 --zone us-central1-a --tunnel-through-iap
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
| `terraform/` | GCP provisioning, including the GitHub Actions identity federation |
| `.github/workflows/deploy.yml` | Build, verify and roll out on push to `main` |
| `deploy/remote-deploy.sh` | Runs on the VM: swaps the image, verifies health, rolls back on failure |
| `AGENTS.md` | Architecture notes for coding agents — layering, conventions, how the pieces connect |

## License

MIT © 2025 Ivo Petković
