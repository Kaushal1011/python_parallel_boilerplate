import json
import zmq
import time
import random


def execute_task(operation, data):
    time.sleep(random.uniform(0.05, 0.2))  # Simulate variable processing time
    """Perform a simple operation on the given data."""
    if operation == "square":
        time.sleep(0.1)
        return data * data
    elif operation == "double":
        time.sleep(0.1)
        return data * 2
    elif operation == "sleep":
        time.sleep(float(data))
        return data
    else:
        return data


def worker_main(task_port: int, result_port: int, worker_id: int = 0):
    """Generic PUB/SUB worker that executes tasks."""
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect(f"tcp://127.0.0.1:{task_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, str(worker_id))

    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect(f"tcp://127.0.0.1:{result_port}")

    print(f"Generic worker {worker_id} listening on {task_port}")
    while True:
        message = sub_socket.recv_string()
        _, payload_json = message.split(" ", 1)
        payload = json.loads(payload_json)
        operation = payload.get("operation")
        data = payload.get("data")
        # print(f"Worker {worker_id} received: {payload}")
        result_data = execute_task(operation, data)
        result = {
            "task_id": payload["task_id"],
            "worker_id": worker_id,
            "result": result_data,
        }
        # print(f"Worker {worker_id} task id {payload['task_id']}")
        pub_socket.send_json(result)
