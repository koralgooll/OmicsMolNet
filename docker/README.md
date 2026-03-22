# Flowise (Docker Compose)

This folder contains a ready-to-run Flowise deployment using `docker compose`.

On first start, Flowise may redirect you to `/organization-setup` to create the
initial admin account. This repo includes an automated bootstrap (`flowise-init`)
that can create the admin account for you when you provide credentials via
`docker/.env` (see `init-flowise.py`).

## Configure Admin Account

Create `docker/.env` from `[docker/.env.example](docker/.env.example)` and set:

- `FLOWISE_ADMIN_NAME`
- `FLOWISE_ADMIN_EMAIL`
- `FLOWISE_ADMIN_PASSWORD`

Optional (enterprise only):

- `FLOWISE_ORG_NAME`

## Start

```sh
docker compose -f docker/docker-compose.yml up -d
```

## Stop

```sh
docker compose -f docker/docker-compose.yml down
```

## Reset (clears persisted data)

```sh
docker compose -f docker/docker-compose.yml down -v
```

Flowise data (flows, credentials, database, uploads) is persisted in the named Docker volume `flowise_data`, mounted to `/root/.flowise` inside the container.

After starting, open: [localhost:3000](http://localhost:3000/)
