# Hermes adapter development: stage 1, manual probe

This PR deliberately does **not** connect Hermes to the job queue yet. It
introduces a small, auditable compatibility probe with fixed input and
no platform credentials.

On Acer, after reviewing the code on this branch:

```bash
python3 scripts/probe_hermes.py
# Review displayed command and Hermes tool policy first.
python3 scripts/probe_hermes.py --execute
```

Probe invokes the supported `hermes chat --oneshot --quiet --query-file -` CLI,
using the locally configured `acer-qwen35-64k:latest` model and only
the `clarify` toolset. Confirm `hermes chat --help` on the installed version
before executing. Output is not guaranteed to contain only the answer;
this probe reports whether the text is exactly 56.

## Security boundaries

**This is not a sandbox or a service**. Disabling toolsets does not isolate
the agent from all profile plugins, hooks, or user credentials. Do not
execute against untrusted prompts, user accounts, secrets, or sensitive
files. Do not expose Hermes as a network service. Do not supply
`--yolo`. The live control-plane worker remains unchanged.

## Production adapter gates (separate implementation/review)
1. Separate low-privilege OS user or container, isolated home/profile and workspace.
2. No personal credentials, tools, MCP servers, background gateways, or writable host mounts.
3. Explicit allowlist of task types, payload size limits, resource limits, and request authorization.
4. Per-task process timeout, lease heartbeat, bounded stdout/stderr, cancellation, and error codes.
5. Unit and integration tests including malicious tool use / prompt injection attempts.
6. No remote access until per-worker credentials and transport security are ready.

Do not merge a live Hermes queue worker without these controls.
