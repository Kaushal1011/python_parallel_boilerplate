from fastapi import FastAPI
from typing import List
import zmq.asyncio
import asyncio

app = FastAPI()

# These will be filled by main when starting
worker_ports: List[int] = []
_zmq_context = zmq.asyncio.Context()
_sockets = {}
_rr_counter = 0


def setup_sockets(ports: List[int]):
    global worker_ports, _sockets
    worker_ports = ports
    for port in ports:
        sock = _zmq_context.socket(zmq.REQ)
        sock.connect(f"tcp://127.0.0.1:{port}")
        _sockets[port] = sock


def close():
    """Close all ZeroMQ sockets and terminate the context."""
    for sock in _sockets.values():
        sock.close(0)
    _sockets.clear()
    _zmq_context.term()


@app.post("/process")
async def process_endpoint(payload: dict):
    global _rr_counter
    if not worker_ports:
        return {"error": "No workers available"}
    port = worker_ports[_rr_counter % len(worker_ports)]
    sock = _sockets[port]
    await sock.send_json(payload)
    reply = await sock.recv_json()
    _rr_counter += 1
    return reply
