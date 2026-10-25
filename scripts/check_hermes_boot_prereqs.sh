#!/usr/bin/env bash
# Fail-closed gate for enabling the fixed-task persistent service.
set -euo pipefail
fail(){ echo "BLOCKED: $*" >&2; exit 1; }
[[ "${EUID}" -eq 0 ]] || fail "Run via sudo"
repo="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
id hermes-worker >/dev/null || fail "worker user missing"
groups="$(id -nG hermes-worker)"
for group in docker sudo adm lxd; do
  [[ " $groups " != *" $group "* ]] || fail "privileged group $group"
done
test "$(stat -c '%a %U' /var/lib/hermes-worker)" = "700 hermes-worker" || fail "home permissions"
test "$(stat -c '%a %U' /var/lib/hermes-worker/.config/worker.key)" = "600 hermes-worker" || fail "key permissions"
test -r /opt/agent-platform/scripts/hermes_scoped_worker.py || fail "worker code missing"
[[ -f /etc/systemd/system/hermes-scoped-worker.service ]] || fail "unit missing"
# Cannot start a worker until Hermes is independently installed and configured.
[[ -x /opt/hermes-worker/bin/hermes ]] || fail "isolated Hermes launcher absent"
runuser -u hermes-worker -- env -i HOME=/var/lib/hermes-worker XDG_CONFIG_HOME=/var/lib/hermes-worker/.config PATH=/opt/hermes-worker/bin:/usr/bin:/bin /opt/hermes-worker/bin/hermes chat --help >/dev/null || fail "Hermes launcher not usable"
runuser -u hermes-worker -- env -i HOME=/var/lib/hermes-worker PATH=/usr/bin:/bin curl --noproxy '*' -fsS --max-time 5 http://127.0.0.1:11434/api/tags >/dev/null || fail "Ollama inaccessible"
runuser -u hermes-worker -- test ! -r "$repo/.env" || fail "admin .env readable"
systemd-analyze verify /etc/systemd/system/hermes-scoped-worker.service || fail "invalid systemd unit"
echo "PASS: boot service prerequisites verified (not an end-to-end execution test)"
