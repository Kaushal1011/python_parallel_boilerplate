from fastapi import FastAPI
from typing import List, Any, Dict, Tuple
import zmq.asyncio
import json
import asyncio
import contextlib

app = FastAPI()

_worker_ids: List[int] = []
_task_port: int = 0
_result_port: int = 0
_zmq_context = zmq.asyncio.Context()
_pub_socket = None
_sub_socket = None
_next_worker = 0
_task_counter = 0
_pending: Dict[Tuple[int, int], asyncio.Future] = {}
_listener_task: asyncio.Task | None = None


def setup_sockets(task_port: int, result_port: int, worker_ids: List[int]):
    """Initialize PUB/SUB sockets."""
    global _worker_ids, _task_port, _result_port, _pub_socket, _sub_socket
    _worker_ids = worker_ids
    _task_port = task_port
    _result_port = result_port

    _pub_socket = _zmq_context.socket(zmq.PUB)
    _pub_socket.bind(f"tcp://127.0.0.1:{task_port}")

    _sub_socket = _zmq_context.socket(zmq.SUB)
    _sub_socket.bind(f"tcp://127.0.0.1:{result_port}")
    _sub_socket.setsockopt_string(zmq.SUBSCRIBE, "")


async def _result_listener() -> None:
    """Background task that routes worker results to waiting futures."""
    while True:
        msg = await _sub_socket.recv_json()
        key = (msg.get("task_id"), msg.get("worker_id"))
        fut = _pending.pop(key, None)
        if fut is not None and not fut.done():
            fut.set_result(msg.get("result"))


@app.on_event("startup")
async def _startup() -> None:
    global _listener_task
    if _listener_task is None:
        _listener_task = asyncio.create_task(_result_listener())


@app.on_event("shutdown")
async def _shutdown() -> None:
    global _listener_task
    if _listener_task is not None:
        _listener_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await _listener_task
    _listener_task = None
    close()


def close():
    if _pub_socket is not None:
        _pub_socket.close(0)
    if _sub_socket is not None:
        _sub_socket.close(0)
    _zmq_context.term()


async def send_task(operation: str, data: Any) -> Any:
    global _next_worker, _task_counter
    task_id = _task_counter
    _task_counter += 1
    worker_id = _worker_ids[_next_worker]
    _next_worker = (_next_worker + 1) % len(_worker_ids)

    payload = {
        "task_id": task_id,
        "worker_id": worker_id,
        "operation": operation,
        "data": data,
    }
    message = f"{worker_id} {json.dumps(payload)}"

    fut = asyncio.get_running_loop().create_future()
    _pending[(task_id, worker_id)] = fut
    await _pub_socket.send_string(message)
    return await fut


@app.post("/task")
async def task_endpoint(payload: dict):
    if not _worker_ids:
        return {"error": "No workers available"}
    operation = payload.get("operation")
    data = payload.get("data")
    result = await send_task(operation, data)
    return {"result": result}
