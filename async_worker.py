import sys
import asyncio
import zmq.asyncio

async def async_task(value: int, delay: float = 0.1) -> int:
    """Simulate an async operation for demonstration."""
    await asyncio.sleep(delay)
    return value * value

async def handle_request(payload: dict) -> dict:
    """Process multiple values concurrently using asyncio."""
    values = payload.get("values", [])
    tasks = [async_task(v) for v in values]
    results = await asyncio.gather(*tasks)
    return {"results": results}

async def worker_main(port: int, worker_id: int = 0):
    """Entry point for the async worker."""
    context = zmq.asyncio.Context()
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://127.0.0.1:{port}")
    print(f"Async worker {worker_id} listening on port {port}")
    while True:
        message = await socket.recv_json()
        print(f"Async worker {worker_id} received: {message}")
        result = await handle_request(message)
        response = {"worker_id": worker_id, **result}
        await socket.send_json(response)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python async_worker.py <port> [worker_id]")
        sys.exit(1)
    port = int(sys.argv[1])
    worker_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    asyncio.run(worker_main(port, worker_id))
