from fastapi import FastAPI
from typing import List
import zmq.asyncio
import asyncio

app = FastAPI()

# These will be filled by main when starting
worker_ports: List[int] = []
_zmq_context = zmq.asyncio.Context()
_sockets = {}
_pub_socket = None
_rr_counter = 0
_pattern = "reqrep"


def setup_sockets(ports: List[int], pattern: str = "reqrep"):
    """Create sockets based on the configured communication pattern."""
    global worker_ports, _sockets, _pub_socket, _pattern
    worker_ports = ports
    _pattern = pattern
    if pattern == "reqrep":
        for port in ports:
            sock = _zmq_context.socket(zmq.REQ)
            sock.connect(f"tcp://127.0.0.1:{port}")
            _sockets[port] = sock
    elif pattern == "pubsub":
        # For pub/sub we only use the first port.
        port = ports[0]
        _pub_socket = _zmq_context.socket(zmq.PUB)
        _pub_socket.bind(f"tcp://127.0.0.1:{port}")
    else:
        raise ValueError(f"Unknown pattern: {pattern}")


def close():
    """Close all ZeroMQ sockets and terminate the context."""
    for sock in _sockets.values():
        sock.close(0)
    if _pub_socket is not None:
        _pub_socket.close(0)
    _sockets.clear()
    _zmq_context.term()


@app.post("/process")
async def process_endpoint(payload: dict):
    global _rr_counter
    if not worker_ports:
        return {"error": "No workers available"}
    if _pattern == "reqrep":
        port = worker_ports[_rr_counter % len(worker_ports)]
        sock = _sockets[port]
        await sock.send_json(payload)
        reply = await sock.recv_json()
        _rr_counter += 1
        return reply
    elif _pattern == "pubsub":
        await _pub_socket.send_json(payload)
        return {"status": "published"}
    else:
        return {"error": f"Unknown pattern: {_pattern}"}

