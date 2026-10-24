# Agent Platform

General-purpose infrastructure for durable automation and distributed agents. PhD Scout is an application, not a dependency of this platform.

## Current milestone

This repository contains a minimal, model-independent control plane with:
- FastAPI v1 projects and jobs, authenticated by a private API key
- PostgreSQL task state, idempotent job submission and capability-aware worker claims
- Lease heartbeats, retry recovery and terminal job events
- A bounded reference worker supporting core.echo and core.add only
- Docker Compose for the Acer Nitro (CPU-only; no Ollama/CUDA needed)
- CI unit checks and an end-to-end smoke test for the Acer

Not implemented yet: Slack bot/notifications delivery, approvals, multi-tenant identity, remote-worker credentials, Hermes, model routing, PhD Scout integration, dashboard or durable workflow DAGs. The events table is preparation for proactive communication, not a functioning Slack adapter.

## PR and deployment flow

1. Review the open bootstrap PR and check CI in GitHub.
2. Merge the PR into main when satisfied.
3. On the Acer (Ubuntu 26.04.1 with Docker Engine and Compose already installed):

    git clone https://github.com/WAniruddha/agent-platform.git ~/projects/agent-platform

    cd ~/projects/agent-platform

    python3 scripts/init_env.py

    sudo docker compose config --quiet

    sudo docker compose up -d --build

    sudo docker compose ps

    bash scripts/smoke.sh

4. Expect the final line SMOKE TEST PASSED. If not, inspect sudo docker compose logs --tail=100 api worker migrate reaper db.

The .env file is unique to the Acer and ignored by Git. Never paste it into chats or commit it. The project is currently public.

## Remote access

API available only at http://127.0.0.1:8765 on the Acer. For LAN administration use SSH tunnelling after SSH is enabled:

    ssh -N -L 8765:127.0.0.1:8765 awadekar@ACER_LAN_IP

Do not expose the API or PostgreSQL with public port forwarding. Worker authentication is still a shared key, so this milestone is suitable only for your trusted local setup.

## Local workflow

After merging a tested change, update without deleting the database:

    cd ~/projects/agent-platform
    git fetch origin
    git switch main
    git pull --ff-only
    sudo docker compose up -d --build
    bash scripts/smoke.sh

Use sudo docker compose down to stop services; never use down -v unless discarding PostgreSQL data.

Design and security limits: docs/architecture.md.

Future adapters may include Slack, Telegram, a web dashboard and remote inference workers, while keeping infrastructure framework-neutral.
