import asyncio
import os
import signal
import subprocess
import sys

import httpx
import uvicorn
from fastapi import FastAPI, Request, Response

# ACE-Step runs on the inner port; RunPod talks to the wrapper on PORT.
INNER_PORT = 8001
OUTER_PORT = int(os.getenv("PORT", "8001"))

# Start ACE-Step as a subprocess
ace_process = subprocess.Popen(
    [
        sys.executable,
        "acestep/api_server.py",
        "--host", "127.0.0.1",
        "--port", str(INNER_PORT),
    ],
    cwd="/workspace/ACE-Step-1.5",
)

app = FastAPI()


@app.get("/ping")
async def ping():
    # Always return 200 immediately so RunPod marks the worker healthy.
    return {"status": "healthy"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(request: Request, path: str):
    url = f"http://127.0.0.1:{INNER_PORT}/{path}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            upstream = await client.request(
                request.method,
                url,
                content=body,
                headers=headers,
                params=request.query_params,
            )
            return Response(
                content=upstream.content,
                status_code=upstream.status_code,
                headers={
                    k: v
                    for k, v in upstream.headers.items()
                    if k.lower() not in ("content-encoding", "transfer-encoding", "connection")
                },
            )
        except httpx.ConnectError:
            return Response(
                content=b'{"error": "ACE-Step is still starting up"}',
                status_code=503,
                media_type="application/json",
            )


def _shutdown(*_):
    ace_process.terminate()
    try:
        ace_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        ace_process.kill()
    sys.exit(0)


signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=OUTER_PORT)
