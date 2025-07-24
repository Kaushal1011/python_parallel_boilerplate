# Python Parallel Boilerplate

This repository provides a small but flexible example of how to combine a
FastAPI server with multiple worker processes communicating via ZeroMQ.

## Overview

`main.py` starts a FastAPI application and a configurable number of worker
processes. Each worker listens on its own ZeroMQ `REP` socket. The FastAPI
server forwards API requests to the workers over `REQ` sockets using a
round‑robin strategy. Workers are loaded dynamically which makes it easy to
reuse the boilerplate for different kinds of tasks.

The setup is intentionally simple and intended as a starting point for more complex multiprocessing systems.

## Files

- `config.json` – defines how many workers to start, their modules and the
  base port for ZeroMQ sockets.
- `worker.py` – example worker module. Receives JSON messages and echoes them
  back. Use it as a template for your own workers.
- `server.py` – FastAPI application that sends incoming requests to workers via ZeroMQ.
- `main.py` – reads the configuration, launches workers, and runs the FastAPI server.

## Running

Install the dependencies inside a virtual environment and run the main script:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

By default the API server listens on `http://localhost:8000`. Send a POST
request to `/process` with any JSON payload and it will be processed by one of
the workers.

## Configuration

Workers are defined in `config.json`. Each entry specifies the module to import
and optionally the entrypoint function that should be executed in a separate
process.

```json
{
  "zmq_start_port": 6000,
  "api_port": 8000,
  "workers": [
    {"module": "worker", "entrypoint": "worker_main", "replicas": 2}
  ]
}
```

You can point the launcher to a different configuration using:

```bash
python main.py --config my_config.json
```
