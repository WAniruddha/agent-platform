# Isolated Hermes runtime, checkpoint 1

PR stages **read-only runtime checks**, not an installation of Hermes or
an enabled persistent worker. The current native account has already been
created using the preceding identity provisioner.

## On the Acer

```bash
cd ~/agent-platform
git fetch origin
git switch --track origin/feat/hermes-isolated-runtime-probe
bash -n scripts/check_hermes_runtime_isolation.sh
bash scripts/check_hermes_runtime_isolation.sh
sudo -u hermes-worker env -i HOME=/var/lib/hermes-worker PATH=/usr/bin:/bin \
  python3 scripts/hermes_worker_runtime_env_check.py
```

The shell probe requires sudo for checking the isolated identity. It
intentionally fails if the service user can read the operator's Hermes config
or platform `.env`, or if local Ollama is inaccessible.

## Important limits

The read-only checks do NOT prove complete filesystem sandboxing. Native
Linux discretionary access control can leave other paths accessible; systemd
hardening, explicit mounts and network restrictions still need verification.

Do not copy `/home/awadekar/.hermes` to the worker home. Do not install an
unreviewed agent binary or configure any unattended tools. A separate
runtime installation and minimal provider config are the next steps, after
the probes pass and Hermes' required files can be identified.

Do not enable any systemd service or grant the new account Docker access.
