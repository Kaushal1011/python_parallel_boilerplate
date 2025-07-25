# Python Parallel Boilerplate

This repository provides a minimal framework for building parallel back‑end
programs in Python.  A generic launcher starts a FastAPI server along with a
configurable set of worker processes that communicate over ZeroMQ.  The
boilerplate can be reused for many kinds of tasks by plugging in your own worker
and server modules.

Two complete examples are included under `examples/`:

* **Merge sort** – demonstrates a distributed merge sort using the PUB/SUB
  pattern.
* **Round robin counter** – shows how to dispatch tasks to workers in a
  round‑robin fashion while sharing a counter using a mutex.

## Running

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Merge sort

Launch the merge sort API server:

```bash
python main.py -c examples/merge_sort/config.json
```

Send a list of numbers to sort:

```bash
curl -X POST http://localhost:8000/sort -H "Content-Type: application/json" \
  -d '{"values": [5, 2, 8, 1, 3]}'
```

The sorted output is written to a file inside the `output` directory.

### Round robin counter

Start the example with:

```bash
python examples/round_robin/main.py
```

Each request to `/increment` is sent to the workers in round‑robin order.
Workers increment a shared counter protected by a `Lock`.  Query the current
value via `/counter`:

```bash
curl -X POST http://localhost:8000/increment -H "Content-Type: application/json" \
  -d '{"value": 1}'
curl http://localhost:8000/counter
```

## Creating your own program

1. Write a worker module with a `worker_main` function.  It should accept at
   least the arguments `port` and `worker_id` (for `reqrep`) or `task_port`,
   `result_port` and `worker_id` (for `pubsub`).
2. Write a server module exposing `create_app(...)` that returns a FastAPI app.
3. Create a configuration JSON file listing your workers and server module.
4. Run `python main.py -c path/to/your_config.json` or call
   `boilerplate.run_server()` directly if you need to pass shared objects.
