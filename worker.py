"""Example worker module for the multiprocessing boilerplate.

This file contains a very small worker implementation that can be
used out of the box or as a template for more complex workers. The
``worker_main`` function will be executed in a separate process by
``main.py``.

The intention is that users copy this file and adapt ``handle_request``
to their needs. Additional threads can be spawned from inside the
function if desired.
"""

import sys
import zmq
import time
import random


def handle_request(payload: dict, worker_id: int = None) -> dict:
    """Process a single request.

    Parameters
    ----------
    payload: dict
        JSON payload received from the API server.

    Returns
    -------
    dict
        The response that will be sent back to the client.  By default
        the payload is simply echoed.
    """

    # In real scenarios this function could do CPU intensive work,
    # call other services or spawn threads.  It must however remain
    # thread safe if threads are used.
    time.sleep(random.uniform(0.1, 1.0))  # Simulate some processing delay
    print(f"Processing payload: {payload} on worker {worker_id}")
    return {"result": payload}


def worker_main(port: int, worker_id: int = 0):
    """Entry point for each worker process."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")
    print(f"Worker {worker_id} listening on port {port}")
    while True:
        message = socket.recv_json()
        print(f"Worker {worker_id} received: {message}")
        result = handle_request(message, worker_id=worker_id)
        response = {"worker_id": worker_id, **result}
        socket.send_json(response)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python worker.py <port> [worker_id]")
        sys.exit(1)
    port = int(sys.argv[1])
    worker_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    worker_main(port, worker_id)
