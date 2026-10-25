# Dedicated Hermes Linux identity (not an enabled service)

This PR creates only an unprivileged system account and private folders.
**No Hermes binaries, models, keys or personal dotfiles are copied.**
It does not enable any unit, modify Docker, or change PostgreSQL.

## Read-only review

```bash
cd ~/agent-platform
bash -n scripts/provision_hermes_identity.sh scripts/check_hermes_identity.sh
bash scripts/provision_hermes_identity.sh
```

Expected: dry-run message. Do not use `--apply` before reviewing the PR.

## Apply after review

```bash
sudo bash scripts/provision_hermes_identity.sh --apply
sudo bash scripts/check_hermes_identity.sh
```

An existing account with privileged group membership causes the script to
refuse, rather than weakening those memberships automatically. The identity
uses `/usr/sbin/nologin` and private `0700` home/workspace.

## Critical next gates

- The scoped worker script still runs Hermes from `Path.home()` and requires
  `HERMES_WORKER_KEY_FILE`. Provision its isolated model configuration and
  install executable access without copying the operator's secrets.
- The API's scoped worker key currently lives in the operator's Compose
  `.env`; provision a separate file readable by the service user only and
  explicitly pass its path in the future unit. Do not give service user access
  to `.env`.
- Check whether Hermes can reach Ollama from this account; read-only HTTP to
  loopback is necessary, but avoid giving it any privileged daemon access.
- The earlier systemd template references /opt/agent-platform and is **not**
  deployable as-is. It must be adapted and verified in a later change.
- Test filesystem denial of operator home, then lease/restart recovery.
- No `systemctl enable` or autonomous prompts at this stage.

The standard admin user may inspect this provisioned account using sudo,
but the service user should never join `docker`, `sudo`, `lxd` or `adm`.
