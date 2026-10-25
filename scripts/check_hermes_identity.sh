#!/usr/bin/env bash
set -euo pipefail
id hermes-worker >/dev/null
groups="$(id -nG hermes-worker)"
for group in docker sudo adm lxd; do
  if [[ " ${groups} " == *" ${group} "* ]]; then
    echo "FAIL: forbidden group ${group}" >&2
    exit 1
  fi
done
test "$(stat -c '%a %U %G' /var/lib/hermes-worker)" = "700 hermes-worker hermes-worker"
test "$(stat -c '%a %U %G' /var/lib/hermes-worker/workspace)" = "700 hermes-worker hermes-worker"
test "$(stat -c '%a %U %G' /etc/agent-platform)" = "750 root hermes-worker"
echo "PASS: dedicated identity and private directories"
echo "NOTE: Hermes isolation, API secrets, inference connectivity and service startup NOT verified."
