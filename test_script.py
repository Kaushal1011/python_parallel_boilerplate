#!/usr/bin/env python
"""Simple end-to-end test for the FastAPI server and worker processes."""

import subprocess
import time
from typing import Any, Dict

import requests

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def start_server() -> subprocess.Popen:
    """Start the server defined in main.py and return the process handle."""
    return subprocess.Popen(["python", "main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def wait_for_server(port: int = SERVER_PORT, timeout: float = 10) -> bool:
    """Wait until the server accepts connections."""
    url = f"http://{SERVER_HOST}:{port}/docs"
    for _ in range(int(timeout * 10)):
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.1)
    return False


def stop_process(proc: subprocess.Popen) -> None:
    """Terminate a process."""
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def send_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/process", json=payload)
    return resp.json()


def main() -> None:
    proc = start_server()
    try:
        if not wait_for_server():
            print("Server failed to start. Output:")
            if proc.stdout:
                print(proc.stdout.read())
            return

        payloads = [{"value": i} for i in range(5)]
        results = []
        for payload in payloads:
            try:
                response = send_request(payload)
            except Exception as exc:
                response = {"error": str(exc)}
            results.append((payload, response))

        for payload, response in results:
            print(f"{payload} -> {response}")
    finally:
        stop_process(proc)


if __name__ == "__main__":
    main()
