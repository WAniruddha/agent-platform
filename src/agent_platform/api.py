"""Versioned, application-neutral control-plane API. No shell execution."""
from hmac import compare_digest
from os import environ
from uuid import UUID, uuid4
from typing import Any

from fastapi import FastAPI, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator

from .db import connect, json_value

app = FastAPI(title="Agent Platform", version="0.1.0")


def authenticated(x_platform_key: str | None = Header(default=None, alias="X-Platform-Key")):
    expected = environ["PLATFORM_API_KEY"]
    if not x_platform_key or not compare_digest(x_platform_key, expected):
        raise HTTPException(401, "Invalid API key")


class ProjectIn(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    description: str = Field(default="", max_length=1000)


class JobIn(BaseModel):
    project_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    task_type: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    capability: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=-10, le=10)
    max_attempts: int = Field(default=3, ge=1, le=10)
    idempotency_key: str | None = Field(default=None, min_length=3, max_length=128)


class ClaimIn(BaseModel):
    worker_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")
    capabilities: list[str] = Field(min_length=1, max_length=30)
    lease_seconds: int = Field(default=120, ge=30, le=3600)


class HeartbeatIn(BaseModel):
    worker_id: str
    lease_seconds: int = Field(default=120, ge=30, le=3600)


class CompleteIn(BaseModel):
    worker_id: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = Field(default=None, max_length=2000)


class EventIn(BaseModel):
    project_id: str = Field(pattern=r"^[a-z][a-z0-9_-]{1,62}$")
    kind: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,79}$")
    message: str = Field(min_length=1, max_length=450)


@app.get("/healthz")
def health():
    return {"status": "alive", "version": "0.1.0"}


@app.get("/readyz")
def ready():
    try:
        with connect() as db:
            db.execute("SELECT 1")
    except Exception:
        raise HTTPException(503, "Database unavailable") from None
    return {"status": "ready"}


@app.post("/v1/projects", dependencies=[Depends(authenticated)])
def create_project(body: ProjectIn):
    with connect() as db:
        return db.execute(
            """INSERT INTO projects(id,description) VALUES(%s,%s)
               ON CONFLICT(id) DO UPDATE SET description=EXCLUDED.description
               RETURNING id,description,created_at""",
            (body.id, body.description)
        ).fetchone()


@app.get("/v1/projects", dependencies=[Depends(authenticated)])
def projects():
    with connect() as db:
        return db.execute("SELECT * FROM projects ORDER BY id").fetchall()


@app.post("/v1/jobs", dependencies=[Depends(authenticated)])
def submit(body: JobIn):
    with connect() as db:
        if not db.execute("SELECT 1 FROM projects WHERE id=%s", (body.project_id,)).fetchone():
            raise HTTPException(404, "Project not found")
        row = db.execute(
            """INSERT INTO jobs(id,project_id,task_type,capability,payload,
                                 priority,max_attempts,idempotency_key)
               VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT DO NOTHING RETURNING *""",
            (uuid4(), body.project_id, body.task_type, body.capability,
             json_value(body.payload), body.priority, body.max_attempts, body.idempotency_key),
        ).fetchone()
        if row:
            return row
        if body.idempotency_key is None:
            raise HTTPException(409, "Job submission conflict")
        old = db.execute("SELECT * FROM jobs WHERE project_id=%s AND idempotency_key=%s",
                         (body.project_id, body.idempotency_key)).fetchone()
        if old is None or any(old[key] != getattr(body,key) for key in
                              ("task_type","capability","payload","priority","max_attempts")):
            raise HTTPException(409, "Idempotency key reused for different job")
        return old


@app.get("/v1/jobs", dependencies=[Depends(authenticated)])
def jobs(limit: int = 30):
    with connect() as db:
        return db.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s",
                          (max(1,min(limit,100)),)).fetchall()


@app.get("/v1/jobs/{job_id}", dependencies=[Depends(authenticated)])
def job(job_id: UUID):
    with connect() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=%s", (job_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Job not found")
    return row


@app.post("/v1/workers/claim", dependencies=[Depends(authenticated)])
def claim(body: ClaimIn):
    with connect() as db:
        db.execute(
            """INSERT INTO workers(id,capabilities) VALUES(%s,%s)
               ON CONFLICT(id) DO UPDATE SET
                 capabilities=EXCLUDED.capabilities,last_seen_at=now()""",
            (body.worker_id, json_value(body.capabilities)))
        row = db.execute(
            """WITH selected AS (
                 SELECT id FROM jobs
                 WHERE status='queued' AND available_at<=now()
                       AND capability=ANY(%s)
                 ORDER BY priority DESC,created_at,id
                 FOR UPDATE SKIP LOCKED LIMIT 1
               )
               UPDATE jobs j SET status='running',attempts=attempts+1,
                   worker_id=%s,lease_expires_at=now()+(%s * interval '1 second'),
                   updated_at=now()
               FROM selected WHERE j.id=selected.id RETURNING j.*""",
            (body.capabilities, body.worker_id, body.lease_seconds)
        ).fetchone()
    return {"job": row}


@app.get("/v1/workers", dependencies=[Depends(authenticated)])
def workers():
    with connect() as db:
        return db.execute("SELECT * FROM workers ORDER BY last_seen_at DESC").fetchall()


@app.post("/v1/jobs/{job_id}/heartbeat", dependencies=[Depends(authenticated)])
def heartbeat(job_id: UUID, body: HeartbeatIn):
    with connect() as db:
        row = db.execute(
            """UPDATE jobs SET lease_expires_at=now()+(%s * interval '1 second'),updated_at=now()
               WHERE id=%s AND worker_id=%s AND status='running'
                     AND lease_expires_at>now() RETURNING id""",
            (body.lease_seconds,job_id,body.worker_id)).fetchone()
        if row:
            db.execute("UPDATE workers SET last_seen_at=now() WHERE id=%s",(body.worker_id,))
    if not row:
        raise HTTPException(409, "Lease expired or worker mismatch")
    return {"renewed": True}


@app.post("/v1/jobs/{job_id}/complete", dependencies=[Depends(authenticated)])
def complete(job_id: UUID, body: CompleteIn):
    with connect() as db:
        if body.success:
            row = db.execute(
                """UPDATE jobs SET status='succeeded',result=%s,error=NULL,worker_id=NULL,
                            lease_expires_at=NULL,updated_at=now()
                   WHERE id=%s AND worker_id=%s AND status='running'
                         AND lease_expires_at>now()
                   RETURNING id,project_id,status,attempts""",
                (json_value(body.result or {}),job_id,body.worker_id)).fetchone()
        else:
            row = db.execute(
                """UPDATE jobs SET
                      status=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,
                      error=%s,result=NULL,worker_id=NULL,lease_expires_at=NULL,
                      available_at=now()+(LEAST(300,POWER(2,attempts)::int * 5) * interval '1 second'),
                      updated_at=now()
                   WHERE id=%s AND worker_id=%s AND status='running'
                         AND lease_expires_at>now()
                   RETURNING id,project_id,status,attempts""",
                (body.error or "Worker reported failure",job_id,body.worker_id)).fetchone()
        if not row:
            raise HTTPException(409, "Lease expired or worker mismatch")
        if row["status"] in ("succeeded", "failed"):
            db.execute(
                """INSERT INTO events(id,project_id,kind,message)
                   VALUES(%s,%s,%s,%s)""",
                (uuid4(),row["project_id"],"job."+row["status"],
                 "Job "+str(row["id"])+" "+row["status"]))
    return row


@app.post("/v1/events", dependencies=[Depends(authenticated)])
def event(body: EventIn):
    with connect() as db:
        if not db.execute("SELECT 1 FROM projects WHERE id=%s",(body.project_id,)).fetchone():
            raise HTTPException(404, "Project not found")
        return db.execute(
            """INSERT INTO events(id,project_id,kind,message)
               VALUES(%s,%s,%s,%s) RETURNING id,status""",
            (uuid4(),body.project_id,body.kind,body.message)).fetchone()


@app.get("/v1/events", dependencies=[Depends(authenticated)])
def events(limit: int = 30):
    with connect() as db:
        return db.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT %s",
                          (max(1,min(limit,100)),)).fetchall()

# Agent entries are descriptions only. They do not grant task execution,
# permit arbitrary commands, or confer independent worker credentials.
class AgentIn(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_-]{2,62}$")
    runtime: str = Field(pattern=r"^[a-z][a-z0-9_.-]{1,63}$")
    description: str = Field(default="", max_length=1000)
    capabilities: list[str] = Field(min_length=1, max_length=30)

    @field_validator("capabilities")
    @classmethod
    def validate_capabilities(cls, values):
        import re
        if len(set(values)) != len(values) or any(
            re.fullmatch(r"[a-z][a-z0-9_.-]{2,79}", item) is None
            for item in values
        ):
            raise ValueError("Capabilities must be unique valid identifiers")
        return values


@app.post("/v1/agents", dependencies=[Depends(authenticated)])
def register_agent(body: AgentIn):
    """Register metadata only. New agents cannot execute jobs."""
    with connect() as db:
        return db.execute(
            """INSERT INTO agents(id,runtime,description,capabilities)
               VALUES(%s,%s,%s,%s)
               ON CONFLICT(id) DO UPDATE SET
                 runtime=EXCLUDED.runtime,
                 description=EXCLUDED.description,
                 capabilities=EXCLUDED.capabilities,
                 updated_at=now()
               RETURNING *""",
            (body.id, body.runtime, body.description, json_value(body.capabilities))
        ).fetchone()


@app.get("/v1/agents", dependencies=[Depends(authenticated)])
def list_agents():
    with connect() as db:
        return db.execute("SELECT * FROM agents ORDER BY id").fetchall()


@app.get("/v1/agents/{agent_id}", dependencies=[Depends(authenticated)])
def get_agent(agent_id: str):
    with connect() as db:
        row = db.execute("SELECT * FROM agents WHERE id=%s", (agent_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Agent not found")
    return row


# Explicitly separate narrow worker endpoints from administrator authentication.
from .hermes_scoped import router as hermes_demo_router
app.include_router(hermes_demo_router)
