#!/usr/bin/env bash
# Read-only verification. No secrets printed, no service started.
set -euo pipefail
if ! id hermes-worker >/dev/null 2>&1; then
  echo "BLOCKED: hermes-worker user absent"; exit 1
fi
account_home="$(getent passwd hermes-worker | cut -d: -f6)"
if [[ "$account_home" != "/var/lib/hermes-worker" ]]; then
  echo "BLOCKED: Unexpected account home"; exit 1
fi
if sudo -u hermes-worker test -r "$HOME/.hermes/config.yaml"; then
  echo "BLOCKED: service user can read operator Hermes configuration"; exit 1
fi
if sudo -u hermes-worker test -r "$HOME/agent-platform/.env"; then
  echo "BLOCKED: service user can read platform administrator secrets"; exit 1
fi
echo "PASS: selected operator configuration files are not readable"
response="$(sudo -u hermes-worker curl --noproxy '*' -fsS --max-time 8 http://127.0.0.1:11434/api/tags)" || {
  echo "BLOCKED: worker cannot reach loopback Ollama"; exit 1;
}
printf '%s' "$response" | python3 -c 'import json,sys; models=json.load(sys.stdin).get("models",[]); assert isinstance(models,list); print("PASS: Ollama accessible; model count:",len(models))'
echo "NOTE: These checks do not prove complete filesystem or process isolation."
