from fastapi import APIRouter, Request
router = APIRouter()

@router.post("/webhooks/jenkins")
async def jenkins_webhook(req: Request):
    p = await req.json()
    # extract minimal fields safely
    build = (p.get("build") or {})
    job = p.get("name") or p.get("job_name")
    out = {
        "job": job,
        "number": build.get("number") or p.get("build_number"),
        "result": build.get("status") or p.get("result"),
        "durationMs": build.get("duration") or p.get("duration") or p.get("durationMs"),
        "timestamp": build.get("timestamp") or p.get("timestamp"),
    }
    # TODO: upsert into your storage or cache; optionally broadcast SSE
    return {"status":"ok", **out}

