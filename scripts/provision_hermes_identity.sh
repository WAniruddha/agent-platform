#!/usr/bin/env bash
# Provision only the service account and private directories. Does NOT install,
# configure or start Hermes, copy credentials, or alter Docker/Ollama.
set -euo pipefail
if [[ ${EUID} -ne 0 ]]; then
  echo "Run with sudo after reviewing this script" >&2
  exit 1
fi
if [[ "${1:-}" != "--apply" ]]; then
  echo "Dry-run: would create locked hermes-worker system account and private directories."
  echo "To apply: sudo bash scripts/provision_hermes_identity.sh --apply"
  exit 0
fi

if ! getent group hermes-worker >/dev/null; then
  groupadd --system hermes-worker
fi
if ! id hermes-worker >/dev/null 2>&1; then
  useradd --system --gid hermes-worker --home-dir /var/lib/hermes-worker \
    --create-home --shell /usr/sbin/nologin hermes-worker
fi
# Refuse silently inheriting privileged access if the account already existed.
if id -nG hermes-worker | tr ' ' '\n' | grep -Eq '^(docker|sudo|adm|lxd)$'; then
  echo "Refusing: hermes-worker has privileged group membership" >&2
  exit 1
fi

install -d -o hermes-worker -g hermes-worker -m 0700 /var/lib/hermes-worker
install -d -o hermes-worker -g hermes-worker -m 0700 /var/lib/hermes-worker/.config
install -d -o hermes-worker -g hermes-worker -m 0700 /var/lib/hermes-worker/workspace
install -d -o root -g hermes-worker -m 0750 /etc/agent-platform
echo "Service identity and directories provisioned. No service enabled."
