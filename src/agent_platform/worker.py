"""Reference worker: strictly allowlisted operations via HTTP, no direct DB access."""
import logging
import os
import signal
import threading
import httpx
from .handlers import HANDLERS, dispatch

logging.basicConfig(level=logging.INFO)
LOG=logging.getLogger("worker")
STOP=threading.Event()

def main():
    signal.signal(signal.SIGTERM,lambda *_: STOP.set())
    host=os.environ.get("PLATFORM_API_URL","http://api:8000")
    key=os.environ["PLATFORM_API_KEY"]
    worker_id=os.environ.get("WORKER_ID","acer-light-1")
    caps=[v.strip() for v in os.environ.get("WORKER_CAPABILITIES","core.echo,core.add").split(",") if v.strip()]
    if not caps or any(cap not in HANDLERS for cap in caps):
        raise RuntimeError("Invalid worker capabilities")
    headers={"X-Platform-Key":key}
    with httpx.Client(base_url=host,headers=headers,timeout=15) as client:
        while not STOP.is_set():
            try:
                r=client.post("/v1/workers/claim",json={
                    "worker_id":worker_id,"capabilities":caps,"lease_seconds":120})
                r.raise_for_status()
                job=r.json()["job"]
                if job is None:
                    STOP.wait(3)
                    continue
                job_id=job["id"]
                end_heartbeat=threading.Event()
                def renew():
                    with httpx.Client(base_url=host,headers=headers,timeout=15) as hb:
                        while not end_heartbeat.wait(25):
                            try:
                                x=hb.post("/v1/jobs/"+job_id+"/heartbeat",json={
                                    "worker_id":worker_id,"lease_seconds":120})
                                x.raise_for_status()
                            except Exception:
                                LOG.exception("Heartbeat failed for %s",job_id)
                thread=threading.Thread(target=renew,daemon=True)
                thread.start()
                try:
                    result=dispatch(job["task_type"],job["payload"])
                    data={"worker_id":worker_id,"success":True,"result":result}
                except Exception as exc:
                    LOG.exception("Job failed")
                    data={"worker_id":worker_id,"success":False,"error":str(exc)[:1900]}
                finally:
                    end_heartbeat.set()
                    thread.join(timeout=3)
                done=client.post("/v1/jobs/"+job_id+"/complete",json=data)
                done.raise_for_status()
                LOG.info("job=%s completed status=%s",job_id,done.json()["status"])
            except Exception:
                LOG.exception("Worker connection/execution error")
                STOP.wait(5)

if __name__=="__main__":
    main()
