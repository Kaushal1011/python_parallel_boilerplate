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


def start_workers(config) -> List[int]:
    """Spawn worker processes as described in the configuration."""
    start_port = config.get("zmq_start_port", 6000)
    pattern = config.get("pattern", "reqrep")
    worker_ports = []
    processes = []
    port = start_port
    for worker_conf in config.get("workers", []):
        replicas = worker_conf.get("replicas", 1)
        default_entrypoint = "worker_main" if pattern == "reqrep" else "pubsub_worker_main"
        entrypoint = worker_conf.get("entrypoint", default_entrypoint)
        worker_fn = _load_entrypoint(worker_conf["module"], entrypoint)
        for i in range(replicas):
            p = Process(target=worker_fn, args=(port, i))
            p.daemon = True
            p.start()
            processes.append(p)
            if pattern == "reqrep":
                worker_ports.append(port)
                port += 1
    if pattern == "pubsub":
        # All workers share the same port in pub/sub mode
        worker_ports.append(start_port)
    return worker_ports, processes, pattern


def main(config_path: str):
    config = json.loads(Path(config_path).read_text())
    ports, procs, pattern = start_workers(config)
    server.setup_sockets(ports, pattern)
    print(f"Started workers on ports: {ports}")
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
    parser.add_argument("-c", "--config", default="config.json",
                        help="Path to configuration JSON file")
    args = parser.parse_args()
    main(args.config)
