# Scoped Hermes worker: supervised rollout only

This PR introduces a second, independent **demo-worker credential**. The
administrative `X-Platform-Key` is not accepted by the new
`/v1/hermes-demo/*` routes. The routes fix the worker identity and its only
claimable capability: `hermes.demo.multiply`. The old generic API and existing
Docker worker are unchanged.

## Security boundary and limitations

This is **not** a complete service sandbox:
- The worker still launches Hermes under the invoking Unix user's home/profile.
- A worker token can only use the dedicated claim/heartbeat/complete routes,
  but any holder of it can potentially impersonate this demo worker.
- The API credential must remain secret; never paste it into a chat.
- There is no general-purpose prompt execution and no enabled systemd unit.

## Acer steps, only after branch review

1. On the Acer, check out this branch and run Python tests.
2. To enable the scoped API, generate a separate worker credential and append
   it to the local operator-controlled `.env` with mode 0600. Keep it out of Git.

   ```bash
   cd ~/agent-platform
   python3 - <<'PY'
   from pathlib import Path
   import secrets
   env = Path(".env")
   assert env.is_file()
   assert "HERMES_WORKER_KEY=" not in env.read_text()
   key = secrets.token_urlsafe(48)
   with env.open("a") as f:
       f.write("\\nHERMES_WORKER_KEY=" + key + "\\n")
   Path("/tmp/hermes-worker-key-stage").write_text(key + "\\n")
   PY
   chmod 600 .env /tmp/hermes-worker-key-stage
   ```

   **Do not run the staged-key steps without first reviewing where keys are
   persisted.** The template intentionally avoids printing keys.

3. Once the API is rebuilt with the new environment variable, test the
   authorization boundary: a wrong worker key must return 401 and the
   normal admin key must not grant scoped-worker access.
4. Do not start automatic service operation. The dedicated user, isolated
   home/profile, and filesystem checks still need a separate rollout.

Rollback: remove the staged key file and unset the new local env variable,
then restart only the affected API after deciding whether credential rotation
is necessary. Never use `docker compose down -v`.
