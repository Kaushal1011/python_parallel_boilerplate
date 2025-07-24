"""Entry point that launches worker processes and the API server."""

import json
import importlib
from multiprocessing import Process
import uvicorn
from pathlib import Path
from typing import List, Callable

import server


def _load_entrypoint(module_name: str, entrypoint: str) -> Callable:
    """Import ``entrypoint`` from ``module_name``."""
    module = importlib.import_module(module_name)
    return getattr(module, entrypoint)


def start_workers(config):
    """Spawn worker processes for the distributed merge sort."""
    task_port = config.get("zmq_start_port", 7000)
    result_port = config.get("result_port", task_port + 1)
    workers = []
    processes = []
    worker_id = 0
    for worker_conf in config.get("workers", []):
        replicas = worker_conf.get("replicas", 1)
        entrypoint = worker_conf.get("entrypoint", "worker_main")
        worker_fn = _load_entrypoint(worker_conf["module"], entrypoint)
        for _ in range(replicas):
            p = Process(
                target=worker_fn,
                kwargs={
                    "task_port": task_port,
                    "result_port": result_port,
                    "worker_id": worker_id,
                },
            )
            p.daemon = True
            p.start()
            processes.append(p)
            workers.append(worker_id)
            worker_id += 1
    return workers, processes, task_port, result_port


def main(config_path: str):
    config = json.loads(Path(config_path).read_text())
    worker_ids, procs, task_port, result_port = start_workers(config)
    server.setup_sockets(task_port, result_port, worker_ids)
    print(f"Started workers on port {task_port}")
    host = config.get("host", "0.0.0.0")
    api_port = config.get("api_port", 8000)
    try:
        uvicorn.run(server.app, host=host, port=api_port)
    finally:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Launch API and workers")
    parser.add_argument(
        "-c", "--config", default="config.json", help="Path to configuration JSON file"
    )
    args = parser.parse_args()
    main(args.config)
