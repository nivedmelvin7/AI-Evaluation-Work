# Deploy with Docker Compose and Cloudflare Tunnel

## What Cloudflare does in this deployment

Cloudflare Tunnel is the public ingress; it does not run the Python application,
worker, or PostgreSQL database. Deploy those containers to a persistent Linux
host first, then run `cloudflared` beside them. The tunnel makes outbound-only
connections, so the host does not need inbound HTTP/HTTPS ports open.

The production topology is:

```text
Browser -> Cloudflare -> cloudflared -> app:8000
                                      -> worker -> OpenRouter
                              app/worker -> PostgreSQL volume
```

Cloudflare's current documentation for this model is:

- <https://developers.cloudflare.com/tunnel/routing/>
- <https://developers.cloudflare.com/tunnel/advanced/tunnel-tokens/>
- <https://developers.cloudflare.com/tunnel/downloads/update-cloudflared/>

## Prerequisites

- A Linux host with persistent storage, Git, Docker Engine, and Docker Compose v2.
- A domain using Cloudflare DNS.
- An OpenRouter API key.
- A recent database backup before upgrading an existing installation.

Do not deploy PostgreSQL to an ephemeral filesystem. The Compose stack uses the
named `postgres_data` volume and does not publish PostgreSQL to the host.

## 1. Prepare production configuration

Clone the reviewed branch, then create a private environment file:

```bash
cp .env.example .env
chmod 600 .env
```

Set at least these values in `.env`:

```dotenv
OPENROUTER_API_KEY=replace-me
APP_ENVIRONMENT=production
APP_DEBUG=false
SECRET_KEY=replace-with-at-least-32-random-characters
FRONTEND_URL=https://evaluate.example.com
ENABLE_API_DOCS=false
LOG_TO_FILE=false

AUTH_COOKIE_SECURE=true
ALLOW_PUBLIC_SIGNUP=false
GOOGLE_REDIRECT_URI=https://evaluate.example.com/api/v1/auth/google/callback

POSTGRES_USER=replace-me
POSTGRES_PASSWORD=replace-with-a-long-random-password
POSTGRES_DB=eval_platform
DATABASE_SSL_REQUIRED=false

MAX_UPLOAD_BYTES=10485760
MAX_ACTIVE_EVALUATIONS_PER_USER=2
WORKER_MAX_ATTEMPTS=2
WORKER_STALE_AFTER_SECONDS=3600
```

Generate independent random values for `SECRET_KEY` and `POSTGRES_PASSWORD`.
Leave Google client values empty when Google sign-in is not required. Do not
commit `.env`; production startup deliberately fails on unsafe settings.

Validate Compose syntax without printing the resolved secrets:

```bash
docker compose config -q
```

## 2. Build and start the application

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 migrate app worker postgres
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/ready
```

`migrate` must exit with code 0, while `postgres`, `app`, and `worker` should be
running. The readiness request must return HTTP 200 before configuring public
traffic. The application port is bound only to host loopback.

Create the first account without opening public registration. The command
prompts for the password, so it is not stored in shell history:

```bash
docker compose run --rm app python -m app.create_user \
  --username reviewer \
  --email reviewer@example.com \
  --display-name "Deployment Reviewer"
```

## 3. Create and connect the Cloudflare Tunnel

1. In Cloudflare, open **Networking > Tunnels** and create a remotely managed
   tunnel. Choose the Docker connector instructions.
2. Add a published application route for the chosen hostname, such as
   `evaluate.example.com`.
3. Set the service URL to `http://app:8000`. This is the Compose service name;
   `localhost` would point at the `cloudflared` container itself.
4. Copy only the tunnel token. Treat it as a secret: anyone who has it can run
   the tunnel.
5. Store the token in the ignored secret file without putting it on a command
   line:

```bash
install -d -m 700 .secrets
read -rsp "Cloudflare Tunnel token: " TUNNEL_SECRET
echo
umask 077
printf '%s' "$TUNNEL_SECRET" > .secrets/cloudflare_tunnel_token
unset TUNNEL_SECRET
```

Start the connector with the override file:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml up -d cloudflared
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml ps
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml logs --tail=100 cloudflared
```

No origin TLS override is required because the tunnel-to-app hop uses HTTP on
the private Compose network. Browser-to-Cloudflare traffic remains HTTPS.

## 4. Verify before announcing the deployment

Run all of these checks; a single browser load is not sufficient:

```bash
curl --fail --silent --show-error https://evaluate.example.com/api/v1/health/ready
curl --head https://evaluate.example.com/
docker compose ps
docker compose logs --since=10m app worker postgres
```

Also verify from a different network or a public DNS resolver that the hostname
resolves and HTTPS succeeds. Sign in with the bootstrap account, upload a small
test document, wait for a completed result, then confirm that app and worker
logs contain no unhandled errors. The application rejects files larger than
10 MiB with HTTP 413. Cloudflare's zone-level maximum upload size must remain
above 10 MiB to allow for multipart form overhead (the default plan limits are
already higher).

## 5. Backup and upgrade gate

Before every migration or image upgrade, create and validate a logical backup:

```bash
install -d -m 700 backups
BACKUP_FILE="backups/eval-platform-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
docker compose exec -T postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  | gzip -9 > "$BACKUP_FILE"
gzip -t "$BACKUP_FILE"
test -s "$BACKUP_FILE"
```

For a meaningful preservation check, restore that file into a temporary
database on a non-production host (preferred), or into a deliberately named
temporary database on the same PostgreSQL instance, and inspect key row counts.
Do not proceed with an upgrade until the restore succeeds.

This same-host rehearsal uses an isolated database name and then removes only
that temporary database:

```bash
docker compose exec -T postgres sh -c \
  'dropdb --if-exists -U "$POSTGRES_USER" eval_platform_restore_check'
docker compose exec -T postgres sh -c \
  'createdb -U "$POSTGRES_USER" eval_platform_restore_check'
gzip -dc "$BACKUP_FILE" | docker compose exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d eval_platform_restore_check'
docker compose exec -T postgres sh -c \
  'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d eval_platform_restore_check -c \
  "SELECT count(*) AS users FROM users; SELECT count(*) AS sessions FROM sessions; \
  SELECT count(*) AS versions FROM evaluation_versions;"'
docker compose exec -T postgres sh -c \
  'dropdb -U "$POSTGRES_USER" eval_platform_restore_check'
```

Then deploy the reviewed commit:

```bash
git fetch --all --prune
git checkout <reviewed-branch-or-tag>
git pull --ff-only
docker compose build --pull
docker compose up -d
docker compose ps
curl --fail --silent --show-error http://127.0.0.1:8000/api/v1/health/ready
curl --fail --silent --show-error https://evaluate.example.com/api/v1/health/ready
```

The database migration is forward-moving. Keep the previous image reference and
the verified backup until the application, login, upload, worker completion,
and result retrieval checks all pass.

## Go/no-go checklist

Go only when all items are true:

- `.env` is private and production validation passes.
- A restore-tested backup exists for an upgrade with existing data.
- `migrate` exited successfully and the current Alembic head is applied.
- `app`, `worker`, and `postgres` are healthy/running.
- Local readiness and public HTTPS readiness both return HTTP 200.
- PostgreSQL has no published host port.
- A signed-in 10 MiB-or-smaller test upload completes through the worker.
- A larger-than-10 MiB upload is rejected.
- The tunnel token, OpenRouter key, database password, OAuth secret, and session
  secret do not appear in Git or logs.

Anything else is a no-go until the failed check is resolved.
