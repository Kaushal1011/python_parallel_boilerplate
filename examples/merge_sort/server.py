from fastapi import FastAPI
from typing import List
import zmq.asyncio
import asyncio
import json
from pathlib import Path
import math

app = FastAPI()

# populated by create_app
_worker_ids: List[int] = []
_task_port: int = 0
_result_port: int = 0
_zmq_context = zmq.asyncio.Context()
_pub_socket = None
_sub_socket = None
_task_counter = 0


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


def create_app(task_port: int, result_port: int, worker_ids: List[int], **_):
    """Factory used by the generic launcher."""
    setup_sockets(task_port, result_port, worker_ids)
    return app


def close():
    """Clean up ZeroMQ sockets."""
    if _pub_socket is not None:
        _pub_socket.close(0)
    if _sub_socket is not None:
        _sub_socket.close(0)
    _zmq_context.term()


def merge(left: List[int], right: List[int]) -> List[int]:
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


async def distribute_sort(values: List[int]) -> str:
    """Split values among workers and collect the sorted result."""
    global _task_counter
    task_id = _task_counter
    _task_counter += 1

    n = max(1, len(_worker_ids))
    chunk_size = math.ceil(len(values) / n)
    for idx, wid in enumerate(_worker_ids):
        chunk = values[idx * chunk_size : (idx + 1) * chunk_size]
        payload = {"task_id": task_id, "worker_id": wid, "chunk": chunk}
        message = f"{wid} {json.dumps(payload)}"
        await _pub_socket.send_string(message)

    sorted_chunks = {}
    while len(sorted_chunks) < n:
        msg = await _sub_socket.recv_json()
        if msg.get("task_id") == task_id:
            sorted_chunks[msg["worker_id"]] = msg.get("sorted", [])

    result = sorted_chunks.get(0, [])
    for i in range(1, n):
        result = merge(result, sorted_chunks.get(i, []))

    Path("output").mkdir(exist_ok=True)
    output_path = Path("output") / f"sort_{task_id}.json"
    output_path.write_text(json.dumps(result))
    return str(output_path)


@app.post("/sort")
async def sort_endpoint(payload: dict):
    if not _worker_ids:
        return {"error": "No workers available"}
    values = payload.get("values", [])
    if not isinstance(values, list):
        return {"error": "values must be a list"}
    output_file = await distribute_sort(values)
    return {"output_file": output_file}


@app.on_event("shutdown")
def _cleanup():
    close()
