from .db import connect

SCHEMA = [
"""CREATE TABLE IF NOT EXISTS projects(
id text PRIMARY KEY,
description text NOT NULL DEFAULT '',
created_at timestamptz NOT NULL DEFAULT now())""",
"""CREATE TABLE IF NOT EXISTS jobs(
id uuid PRIMARY KEY,
project_id text NOT NULL REFERENCES projects(id),
task_type text NOT NULL,
capability text NOT NULL,
payload jsonb NOT NULL,
status text NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','succeeded','failed')),
priority integer NOT NULL DEFAULT 0,
attempts integer NOT NULL DEFAULT 0,
max_attempts integer NOT NULL DEFAULT 3,
idempotency_key text,
worker_id text,
lease_expires_at timestamptz,
available_at timestamptz NOT NULL DEFAULT now(),
result jsonb,
error text,
created_at timestamptz NOT NULL DEFAULT now(),
updated_at timestamptz NOT NULL DEFAULT now(),
UNIQUE(project_id,idempotency_key))""",
"""CREATE INDEX IF NOT EXISTS jobs_queue ON jobs(status,available_at,priority DESC,created_at)""",
"""CREATE TABLE IF NOT EXISTS workers(
id text PRIMARY KEY,
capabilities jsonb NOT NULL,
last_seen_at timestamptz NOT NULL DEFAULT now())""",
"""CREATE TABLE IF NOT EXISTS events(
id uuid PRIMARY KEY,
project_id text NOT NULL REFERENCES projects(id),
kind text NOT NULL,
message text NOT NULL,
status text NOT NULL DEFAULT 'queued',
created_at timestamptz NOT NULL DEFAULT now())""",
]

def main():
    with connect() as conn:
        for statement in SCHEMA: conn.execute(statement)
    print("Schema ready")

if __name__=="__main__":
    main()
