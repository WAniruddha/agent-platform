# Architecture and boundaries

Control node: Acer Nitro AN517-51, native Ubuntu 26.04.1 LTS, 14 GiB usable RAM and 4 GiB GTX 1650. Optional heavier worker: RTX 4070 system.

The platform must not require any model to schedule or complete deterministic work.

- Control plane: FastAPI, durable PostgreSQL state, versioned API, capability matching, priority and retries.
- Execution plane: Workers claim tasks over HTTP. Their tool permissions and implementation are separate from the control plane.
- Inference plane (future): Small local tool routers and remote/heavy inference nodes through model-agnostic adapters.
- Communication plane (next PR): Slack Socket Mode adapter for reactive commands and proactive notifications, with its own restricted key and outbox leases.
- Applications: PhD Scout, coding workflows, research automation and future projects are independent clients.

Current milestone: one trusted operator, localhost-bound API, no shell access and an explicit worker allowlist. The shared platform key is not multi-tenant IAM. Workers have at-least-once execution, not exactly once: clients must make side effects idempotent. Jobs are single tasks, not workflow DAGs. Avoid external-facing exposure until scoped service accounts, approvals, audit logging and transport security are implemented.

Git workflow: short feature branch -> CI -> review -> merge -> Acer deployment -> smoke test. Never store real secrets, personal data, or machine credentials in the repo.

Do not install PostgreSQL outside Docker or use host networking; the database is internal to the Compose network. Docker's published ports can bypass UFW, hence the control API binds to loopback only.

Container restart: unless-stopped. Database stored in named Docker volume. Do not use docker compose down -v unless intentionally destroying the database.

Follow-on milestones: restricted Slack gateway + durable notification delivery; HTTPS/Tailscale access, identity-aware worker credentials; inference gateway/Hermes; observability, tested backups and upgrade/rollback protocol; multi-node workers; project integrations.
