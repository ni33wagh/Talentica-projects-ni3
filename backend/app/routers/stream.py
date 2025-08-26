from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio, json, time

router = APIRouter()

async def sse_gen():
    while True:
        # send a heartbeat; later you can push "refresh" events after syncs
        yield f"data: {json.dumps({'type':'heartbeat','ts':int(time.time())})}\n\n"
        await asyncio.sleep(15)

@router.get("/stream")
def stream():
    return StreamingResponse(sse_gen(), media_type="text/event-stream")

