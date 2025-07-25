from fastapi import FastAPI
from typing import List
import zmq.asyncio

app = FastAPI()

_worker_ports: List[int] = []
_sockets = {}
_rr_counter = 0
_zmq_context = zmq.asyncio.Context()
_counter = None
_lock = None


def setup(ports: List[int], counter, lock):
    global _worker_ports, _counter, _lock
    _worker_ports = ports
    _counter = counter
    _lock = lock
    for port in ports:
        sock = _zmq_context.socket(zmq.REQ)
        sock.connect(f"tcp://127.0.0.1:{port}")
        _sockets[port] = sock


@app.on_event("shutdown")
def close():
    for sock in _sockets.values():
        sock.close(0)
    _sockets.clear()
    _zmq_context.term()


@app.post("/increment")
async def increment(payload: dict):
    global _rr_counter
    if not _worker_ports:
        return {"error": "No workers available"}
    port = _worker_ports[_rr_counter % len(_worker_ports)]
    _rr_counter += 1
    sock = _sockets[port]
    await sock.send_json(payload)
    reply = await sock.recv_json()
    return reply


@app.get("/counter")
def get_counter():
    with _lock:
        value = _counter.value
    return {"counter": value}


def create_app(worker_ids: List[int], counter=None, counter_lock=None, **_):
    setup(worker_ids, counter, counter_lock)
    return app
