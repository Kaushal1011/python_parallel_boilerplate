import json
import zmq


def merge(left, right):
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


def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    return merge(left, right)


def worker_main(task_port: int, result_port: int, worker_id: int = 0):
    """Worker that performs merge sort on chunks of data."""
    context = zmq.Context()
    sub_socket = context.socket(zmq.SUB)
    sub_socket.connect(f"tcp://127.0.0.1:{task_port}")
    sub_socket.setsockopt_string(zmq.SUBSCRIBE, str(worker_id))

    pub_socket = context.socket(zmq.PUB)
    pub_socket.connect(f"tcp://127.0.0.1:{result_port}")

    print(f"MergeSort worker {worker_id} listening on {task_port}")
    while True:
        message = sub_socket.recv_string()
        # Message format: "<id> <json>"
        _, payload_json = message.split(" ", 1)
        payload = json.loads(payload_json)
        print(f"Worker {worker_id} received: {payload}")
        task_id = payload["task_id"]
        chunk = payload.get("chunk", [])
        sorted_chunk = merge_sort(chunk)
        result = {
            "task_id": task_id,
            "worker_id": worker_id,
            "sorted": sorted_chunk,
        }
        print(f"Worker {worker_id} sending sorted chunk: {sorted_chunk}")
        pub_socket.send_json(result)
