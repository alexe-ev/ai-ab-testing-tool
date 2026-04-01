# Deployment

## Prerequisites

- VPS with Docker and Docker Compose installed (Hetzner CX22 or similar, ~5 EUR/mo)
- Domain name pointed at the VPS IP (for HTTPS)

## Quick start

1. Clone the repo:
   ```
   git clone <repo-url>
   cd prompt-ab-testing
   ```

2. Copy the env file and fill in your values:
   ```
   cp .env.example .env
   ```
   Edit `.env`:
   - `DOMAIN` — your domain name (e.g. `example.com`). Use `localhost` for local testing.
   - `OPENAI_API_KEY` — from platform.openai.com
   - `ANTHROPIC_API_KEY` — from console.anthropic.com

3. Start all services:
   ```
   docker compose -f docker-compose.prod.yml up -d --build
   ```

## DNS

Point an A record for your domain to the VPS IP address before starting. Caddy will automatically provision an SSL certificate once DNS propagates.

## SSL

Automatic via Caddy when `DOMAIN` is set to a real domain. No manual certbot setup needed. For local testing, `DOMAIN=localhost` works without SSL.

## Data

SQLite database is stored in the `app_data` Docker volume. It persists across container restarts and updates.

## Updating

```
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Logs

```
docker compose -f docker-compose.prod.yml logs -f
```

To follow a single service:
```
docker compose -f docker-compose.prod.yml logs -f backend
```

## Backup

Copy the data directory from the backend container:
```
docker cp $(docker compose -f docker-compose.prod.yml ps -q backend):/app/data ./backup
```

## Health check

```
curl http://localhost/api/health
```

Expected response: `{"status":"ok"}`
