# Agent registration (PR #2)

This phase introduces **descriptive agent metadata**, not agent execution.

## Existing foundation
- Workers register implicitly on `POST /v1/workers/claim`.
- The scheduler matches *claimed worker capabilities* to queued jobs.
- Only the existing `core.echo` and `core.add` handlers may execute.
- Agents are *not* workers. A future adapter will run inside a worker and map an agent's declared capabilities onto a restricted, verified set of task handlers.

## New API
Authenticated with existing `X-Platform-Key`:
- `POST /v1/agents` registers/upserts an agent descriptor.
- `GET /v1/agents` lists descriptors.
- `GET /v1/agents/{agent_id}` retrieves a descriptor.

Agents are created with `enabled=false`. No endpoint enables them in this phase. Metadata registration does **not** grant worker credentials or execute commands.

## Acer deployment after merge
```bash
cd ~/agent-platform
git pull --ff-only origin main
docker compose up -d --build
bash scripts/smoke.sh
```

The existing migration service adds the agents table while preserving the PostgreSQL volume. Never run `docker compose down -v`.

## Register a disabled Hermes descriptor (optional, after merge)
```bash
cd ~/agent-platform
set -a; source .env; set +a
curl -fsS -X POST http://127.0.0.1:8765/v1/agents \
  -H "X-Platform-Key: $PLATFORM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{"id":"hermes-acer","runtime":"hermes","description":"Planned restricted Hermes runtime","capabilities":["research.web"]}'
unset PLATFORM_API_KEY PLATFORM_DB_PASSWORD
```
Never print or commit `.env`. Keep this API bound to loopback only.

## Next milestone
Build the Hermes worker adapter with restricted handlers, identity-aware credentials, task-level policy and tests. Until then the descriptor is **not an online agent**.
