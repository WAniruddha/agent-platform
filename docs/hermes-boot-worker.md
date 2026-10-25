# Hermes fixed-task persistent worker: boot acceptance plan

This PR adds a real hardened systemd unit and staging installer. It does **not**
install Hermes into the service user or enable automatic startup. The earlier
working personal-account Hermes configuration must not be copied wholesale.

## Review and stage on Acer

```bash
cd ~/agent-platform
git fetch origin
git switch --track origin/feat/hermes-boot-worker
bash -n scripts/install_hermes_boot_worker.sh scripts/check_hermes_boot_prereqs.sh
bash scripts/install_hermes_boot_worker.sh # dry-run only
source .venv/bin/activate
python -m pytest tests/test_hermes_boot_worker.py -v
deactivate
```

After review, run `sudo bash scripts/install_hermes_boot_worker.sh --apply`.
This installs only the fixed-task worker, unit and a copy of the existing
scoped credential. It does not activate the service.

## Isolation gate

Install an independently configured Hermes runtime with a launcher at
`/opt/hermes-worker/bin/hermes` accessible to `hermes-worker`. Give it a
minimal local-only Ollama provider and a separate profile under
`/var/lib/hermes-worker`. Do not copy your operator's `~/.hermes`.
The exact installation and minimal profile format must be checked against the
currently installed Hermes version before provisioning; do not assume that
the existing CLI executable in /home is accessible or safe to share.

Then:

```bash
sudo bash scripts/check_hermes_boot_prereqs.sh
```

**Do not start or enable** while it reports BLOCKED. Even PASS only verifies
prerequisites and systemd syntax. Manually launch one fixed-task test, inspect
the journal and job result, and verify that service cannot access operator
secrets before enabling on boot. Model correctness is distinct from execution.

## Eventual acceptance test (ONLY after runtime setup and supervised checks)

```bash
sudo systemctl enable --now hermes-scoped-worker.service
sudo systemctl status hermes-scoped-worker.service --no-pager
```

Reboot only after manual execution succeeds; submit one authorized
`hermes.demo.multiply` job and verify it reaches `succeeded`. Test reboot
and lease recovery explicitly. Do not use `docker compose down -v`.

The task remains fixed. Enabling general-purpose agent capabilities requires
additional prompt/tool policy and approval work.
