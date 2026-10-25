#!/usr/bin/env bash
# Installs fixed-task worker source, isolated service secret and unit.
# Does NOT start/enable systemd. Requires reviewed separate Hermes runtime.
set -euo pipefail
if [[ "${1:-}" != "--apply" ]]; then
  echo "DRY RUN: would copy fixed-task worker, scoped key and systemd unit."
  echo "After review: sudo bash scripts/install_hermes_boot_worker.sh --apply"
  exit 0
fi
if [[ "${EUID}" -ne 0 ]]; then echo "Run with sudo" >&2; exit 1; fi
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test "$(id -u hermes-worker)" != "0"
[[ "$(getent passwd hermes-worker | cut -d: -f6)" == "/var/lib/hermes-worker" ]] || { echo "Incorrect service home" >&2; exit 1; }
test -f "$repo/.env" || { echo "Missing .env" >&2; exit 1; }

key="$(sed -n 's/^HERMES_WORKER_KEY=//p' "$repo/.env")"
[[ "${#key}" -ge 32 && "$key" != *$'\n'* ]] || { echo "Missing or invalid scoped key" >&2; exit 1; }
umask 077
install -d -o root -g root -m 0755 /opt/agent-platform/scripts
install -o root -g root -m 0644 "$repo/scripts/hermes_scoped_worker.py" /opt/agent-platform/scripts/hermes_scoped_worker.py
install -d -o hermes-worker -g hermes-worker -m 0700 /var/lib/hermes-worker/.config /var/lib/hermes-worker/workspace
secret_tmp="$(mktemp /var/lib/hermes-worker/.config/.worker-key.XXXXXXXX)"
trap 'rm -f "$secret_tmp"; unset key' EXIT
printf '%s\n' "$key" > "$secret_tmp"
chown hermes-worker:hermes-worker "$secret_tmp"
chmod 0600 "$secret_tmp"
mv -f "$secret_tmp" /var/lib/hermes-worker/.config/worker.key
install -o root -g root -m 0644 "$repo/deploy/systemd/hermes-scoped-worker.service" /etc/systemd/system/hermes-scoped-worker.service
systemctl daemon-reload
echo "Staged worker files and unit. Service NOT started or enabled."
