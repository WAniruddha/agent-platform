#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f .env ]] || { echo 'Missing .env. Run python3 scripts/init_env.py'; exit 1; }
KEY="$(sed -n 's/^PLATFORM_API_KEY=//p' .env)"
PORT="$(sed -n 's/^PLATFORM_PORT=//p' .env)"
BASE="http://127.0.0.1:${PORT:-8765}"
auth=(-H "X-Platform-Key: $KEY" -H "Content-Type: application/json")
echo "Health:"
curl -fsS "$BASE/readyz"; echo
echo "Registering example project:"
curl -fsS "${auth[@]}" -d '{"id":"example","description":"Safe smoke-test tasks"}' "$BASE/v1/projects"; echo
nonce="$(date +%s%N)"
echo "Submitting core.add:"
job="$(curl -fsS "${auth[@]}" -d "{\"project_id\":\"example\",\"task_type\":\"core.add\",\"capability\":\"core.add\",\"payload\":{\"numbers\":[2,3,5]},\"idempotency_key\":\"smoke-$nonce\"}" "$BASE/v1/jobs")"
echo "$job"
job_id="$(printf '%s' "$job" | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')"
for i in {1..25}; do
  state="$(curl -fsS "${auth[@]}" "$BASE/v1/jobs/$job_id")"
  if printf '%s' "$state" | python3 -c 'import json,sys; j=json.load(sys.stdin); assert j["status"]=="succeeded" and j["result"]=={"total":10}' 2>/dev/null; then
    echo "$state"
    echo "SMOKE TEST PASSED"
    exit 0
  fi
  if printf '%s' "$state" | python3 -c 'import json,sys; sys.exit(json.load(sys.stdin)["status"]!="failed")'; then
    echo "Job failed: $state"; exit 1
  fi
  sleep 1
done
echo "Timed out waiting for job: $state"; exit 1
