import json
import importlib
from multiprocessing import Process
from pathlib import Path
from typing import Callable, List
import uvicorn


def _load_entrypoint(module_name: str, entrypoint: str) -> Callable:
    module = importlib.import_module(module_name)
    return getattr(module, entrypoint)


def start_workers(config, shared_objects=None):
    pattern = config.get("pattern", "reqrep")
    start_port = config.get("zmq_start_port", 6000)
    result_port = config.get("result_port", start_port + 1)
    worker_ids: List[int] = []
    processes: List[Process] = []
    port = start_port
    for worker_conf in config.get("workers", []):
        replicas = worker_conf.get("replicas", 1)
        entrypoint = worker_conf.get("entrypoint", "worker_main")
        worker_fn = _load_entrypoint(worker_conf["module"], entrypoint)
        for _ in range(replicas):
            kwargs = {"worker_id": len(worker_ids)}
            if pattern == "reqrep":
                kwargs["port"] = port
            else:  # pubsub
                kwargs["task_port"] = start_port
                kwargs["result_port"] = result_port
            if shared_objects:
                kwargs.update(shared_objects)
            p = Process(target=worker_fn, kwargs=kwargs)
            p.daemon = True
            p.start()
            processes.append(p)
            worker_ids.append(port if pattern == "reqrep" else len(worker_ids))
            if pattern == "reqrep":
                port += 1
    if pattern == "pubsub":
        return worker_ids, processes, start_port, result_port
    else:
        return worker_ids, processes, None, None


def run_server(config_path: str, shared_objects=None):
    config = json.loads(Path(config_path).read_text())
    worker_ids, processes, task_port, result_port = start_workers(config, shared_objects)
    server_module = config.get("server_module", "examples.merge_sort.server")
    server = importlib.import_module(server_module)
    app = server.create_app(
        worker_ids=worker_ids,
        task_port=task_port,
        result_port=result_port,
        **(shared_objects or {})
    )
    host = config.get("host", "0.0.0.0")
    api_port = config.get("api_port", 8000)
    try:
        uvicorn.run(app, host=host, port=api_port)
    finally:
        for p in processes:
            p.terminate()
