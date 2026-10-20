"""Recover expired leases, supporting at-least-once delivery."""
import logging
import signal
import threading
from uuid import uuid4
from .db import connect

logging.basicConfig(level=logging.INFO)
STOP=threading.Event()

def sweep():
    with connect() as db:
        rows=db.execute(
            """UPDATE jobs SET
                 status=CASE WHEN attempts>=max_attempts THEN 'failed' ELSE 'queued' END,
                 worker_id=NULL,lease_expires_at=NULL,
                 error='Lease expired; execution outcome unknown',
                 available_at=now()+interval '10 seconds',updated_at=now()
               WHERE status='running' AND lease_expires_at<now()
               RETURNING id,project_id,status"""
        ).fetchall()
        for row in rows:
            if row["status"]=="failed":
                db.execute("INSERT INTO events(id,project_id,kind,message) VALUES(%s,%s,%s,%s)",
                           (uuid4(),row["project_id"],"job.failed",
                            "Job "+str(row["id"])+" failed after lease expiration"))
    return len(rows)

def main():
    signal.signal(signal.SIGTERM,lambda *_:STOP.set())
    while not STOP.is_set():
        try:
            count=sweep()
            if count: logging.warning("Recovered %d expired jobs",count)
        except Exception: logging.exception("Reaper failed")
        STOP.wait(20)

if __name__=="__main__":
    main()
