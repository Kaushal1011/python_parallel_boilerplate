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
source .venv/Scripts/activate
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
  "pattern": "reqrep",  # or "pubsub"
  "workers": [
    {"module": "worker", "entrypoint": "worker_main", "replicas": 2}
  ]
}
```

You can point the launcher to a different configuration using:

```bash
python main.py --config my_config.json
```

## Asyncio worker example

`async_worker.py` demonstrates how to perform concurrent work using `asyncio`.
Instead of handling requests synchronously, it spawns multiple async tasks and
awaits them in parallel using `asyncio.gather`. Enable it by using a
configuration similar to:

```json
{
  "zmq_start_port": 6000,
  "api_port": 8000,
  "workers": [
    {"module": "async_worker", "entrypoint": "worker_main", "replicas": 2}
  ]
}
```

Send a payload containing a list of `values` and each worker will square them
concurrently:

```bash
curl -X POST http://localhost:8000/process -H "Content-Type: application/json" \
  -d '{"values": [1, 2, 3, 4]}'
```

## Generic PUB/SUB task example

`generic_worker.py` and `generic_server.py` show how to distribute arbitrary
tasks using ZeroMQ's PUB/SUB pattern. Each worker subscribes to its ID as the
topic and the server publishes tasks in a round‑robin fashion. A background
listener in the server collects worker results so multiple tasks can be
processed concurrently over a second PUB/SUB socket.

Use the provided `generic_config.json`:

```json
{
  "zmq_start_port": 7000,
  "result_port": 7001,
  "api_port": 8000,
  "server_module": "generic_server",
  "workers": [
    {"module": "generic_worker", "entrypoint": "worker_main", "replicas": 3}
  ]
}
```

Then run:

```bash
python main.py --config generic_config.json
```

Send a task describing the operation and data to process:

```bash
curl -X POST http://localhost:8000/task -H "Content-Type: application/json" \
  -d '{"operation": "square", "data": 5}'
```
