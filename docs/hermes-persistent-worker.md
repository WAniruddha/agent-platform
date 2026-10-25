# Persistent Hermes worker: staging gates

Current state: a proven **supervised** fixed-task queue worker. It runs under
the interactive Ubuntu account and reads the full shared platform API key.
Do **not** install that script as an unattended service yet.

## Staging artifacts

- `deploy/systemd/hermes-worker.service.example`: inactive review template
  for a future dedicated `hermes-worker` operating-system identity.
- `scripts/check_hermes_service_readiness.py`: fail-closed readiness report.
  It intentionally blocks activation until the isolation work is implemented.

## Why not simply `systemctl enable`?

The current demo worker resolves its key from
`~/agent-platform/.env` and invokes Hermes using the caller's home and
profile. A dedicated OS user therefore cannot use it without changes.
Giving a new service the operator's home directory or full platform key
would defeat isolation. `ProtectHome=yes` in the template intentionally
makes that unacceptable shortcut fail.

## Required next changes, before unattended activation

1. Provision dedicated service user with a minimal Hermes install/profile,
   workspace, and independent permissions.
2. Add scoped credentials to API; the existing shared key grants write access
   to the entire platform. Separate worker claim/heartbeat/complete auth.
3. Separate worker configuration from operator home and secrets.
4. Enforce tool restrictions in execution environment (not only in CLI
   arguments). Keep prompt fixed until isolation is tested.
5. Verify boot start, restart, lease recovery and stop semantics.
6. Add resource and output limits; test failure paths.

## Acer check (read-only)

```bash
cd ~/agent-platform
python3 scripts/check_hermes_service_readiness.py || true
python3 -m py_compile scripts/check_hermes_service_readiness.py
```

**Do not copy the unit to systemd or enable it at this stage.**
No Docker changes or database reset are required.
