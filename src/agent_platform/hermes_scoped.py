"""Narrow credentials for the fixed Hermes demonstration worker.

The shared administrator API key is NOT accepted on these endpoints.
These routes grant access only to the fixed demo capability and worker ID.
"""
from hmac import compare_digest
from os import environ
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from .api import ClaimIn, HeartbeatIn, CompleteIn, claim, heartbeat, complete

router = APIRouter(prefix="/v1/hermes-demo", tags=["hermes demo worker"])
WORKER_ID = "acer-hermes-demo-scoped-1"
CAPABILITY = "hermes.demo.multiply"


def scoped_auth(x_worker_key: str | None = Header(default=None, alias="X-Worker-Key")):
    expected = environ.get("HERMES_WORKER_KEY", "")
    if not expected or len(expected) < 32 or not x_worker_key:
        raise HTTPException(401, "Worker credential invalid or not configured")
    if not compare_digest(expected, x_worker_key):
        raise HTTPException(401, "Worker credential invalid")


@router.post("/claim", dependencies=[Depends(scoped_auth)])
def scoped_claim():
    return claim(ClaimIn(worker_id=WORKER_ID, capabilities=[CAPABILITY], lease_seconds=300))


@router.post("/jobs/{job_id}/heartbeat", dependencies=[Depends(scoped_auth)])
def scoped_heartbeat(job_id: UUID):
    return heartbeat(job_id, HeartbeatIn(worker_id=WORKER_ID, lease_seconds=300))


@router.post("/jobs/{job_id}/complete", dependencies=[Depends(scoped_auth)])
def scoped_complete(job_id: UUID, body: CompleteIn):
    if body.worker_id != WORKER_ID:
        raise HTTPException(403, "Worker mismatch")
    return complete(job_id, body)
