# Scoped Hermes worker: review and supervised testing only

This branch adds a separate, independent demo-worker API credential.
The administrative `X-Platform-Key` is not accepted by the new
`/v1/hermes-demo/*` routes. These endpoints fix the worker ID and its
sole claimable capability: `hermes.demo.multiply`.

A new host worker reads its key from `HERMES_WORKER_KEY_FILE`, never the
operator's `.env`. The API reads `HERMES_WORKER_KEY`; if unset or shorter
than 32 characters, the scoped endpoints reject all requests.

## Important limitations

- This remains a supervised demonstration, **not an isolated service**.
- Hermes still runs with the invoking account's permissions and profile.
- A stolen scoped credential could impersonate this one demo worker.
- The current admin API routes and existing Docker worker remain unchanged.
- Do not install/enable the systemd service from PR #8.

## Read-only Acer review

```bash
cd ~/agent-platform
git fetch origin
git switch --track origin/feat/hermes-scoped-worker-auth
python3 -m py_compile scripts/hermes_scoped_worker.py src/agent_platform/hermes_scoped.py
source .venv/bin/activate
python -m pytest tests/test_hermes_scoped_contract.py -v
deactivate
```

**Expected:** tests pass; existing platform remains operational; scoped API
cannot be used until explicitly provisioned with a separate credential.

## Controlled integration rollout (later checkpoint)

Provision the credential using a secret-safe installer, verify directory and
file permissions, then update only the API container using an explicitly
reviewed Compose configuration. Validate rejection of absent/wrong/admin keys,
then claim one fixed task and verify lease and completion behavior.

Only after those checks, provision a dedicated Unix user, isolated Hermes
profile and filesystem boundaries. Never grant the worker read access to the
full platform `.env` or the operator home. Never commit secret values.

Do not run `docker compose down -v`.
