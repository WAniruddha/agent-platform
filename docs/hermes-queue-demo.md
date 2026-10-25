# PR #6: Manual Hermes queue demo

**Status:** local end-to-end integration test, NOT production autonomous operation.

This uses the existing FastAPI/PostgreSQL queue, untouched Docker containers,
and a separate host-side opt-in Hermes worker. Only capability
`hermes.demo.multiply` is claimed. The worker **ignores submitted prompt text**,
rejects payloads other than `{}`, and sends a fixed multiplication question.

## Important security limits

This is **not sandboxed**. Hermes still runs under your normal Ubuntu account
with access to its user profile. Because the queue API uses one shared key,
run the worker only on your trusted local machine and only for the fixed demo
task. Do not run arbitrary user-controlled prompts or add tool privileges yet.
No systemd service or automatic restart is installed.

## Acer steps (do NOT merge or redeploy Docker first)

```bash
cd ~/agent-platform
git fetch origin
git switch feat/hermes-adapter-probe
python3 -m py_compile scripts/hermes_demo_worker.py
python3 scripts/hermes_demo_worker.py
```

After reviewing the file, start the worker in **Terminal 1**:

```bash
python3 scripts/hermes_demo_worker.py --execute
```

In **Terminal 2** submit the demo job using a short-lived shell variable:

```bash
cd ~/agent-platform
KEY="$(sed -n 's/^PLATFORM_API_KEY=//p' .env)"
curl -fsS -X POST http://127.0.0.1:8765/v1/projects \
  -H "X-Platform-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"id":"hermesdemo","description":"Local Hermes adapter test"}'
echo
curl -fsS -X POST http://127.0.0.1:8765/v1/jobs \
  -H "X-Platform-Key: $KEY" -H 'Content-Type: application/json' \
  -d '{"project_id":"hermesdemo","task_type":"hermes.demo.multiply","capability":"hermes.demo.multiply","payload":{},"max_attempts":1}'
echo
curl -fsS http://127.0.0.1:8765/v1/jobs -H "X-Platform-Key: $KEY"
unset KEY
```

Look for the new job with `status=succeeded` and result such as
`{"answer":"56","expected":"56","exact_match":true}`. An answer like
`7 * 8 = 56` still reports `exact_match:false` but is recorded as a
completed model invocation, not a transport failure.

Stop Terminal 1 with Ctrl+C once verified. The reference Docker worker remains
unmodified. The agent descriptor's `enabled=false` is unchanged: it describes
future managed-agent enablement, not this opt-in demonstration process.

**Do not** use `docker compose down -v`.

## Later

For production, run Hermes under a dedicated low-privilege OS identity with
isolated home, explicit profile and tools, filesystem/network boundaries,
scoped worker credential, per-job cancellation, robust output/event parsing,
and audited approvals. Do not enable general prompts until these are in place.
