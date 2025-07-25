import zmq
from multiprocessing import Value, Lock


def worker_main(port: int, worker_id: int = 0, counter: Value = None, counter_lock: Lock = None):
    """Worker that increments a shared counter."""
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")
    print(f"RoundRobin worker {worker_id} listening on port {port}")
    while True:
        message = socket.recv_json()
        value = int(message.get("value", 1))
        with counter_lock:
            counter.value += value
            current = counter.value
        socket.send_json({"worker_id": worker_id, "counter": current})
