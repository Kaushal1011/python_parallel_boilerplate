#!/usr/bin/env python
"""Simple end-to-end test for the FastAPI server and worker processes."""

import subprocess
import time
from typing import Any, Dict
from pathlib import Path

import requests

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8000


def start_server() -> subprocess.Popen:
    """Start the server with the distributed merge sort configuration."""
    return subprocess.Popen([
        "python",
        "main.py",
        "-c",
        "examples/merge_sort/config.json",
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


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
    resp = requests.post(f"http://{SERVER_HOST}:{SERVER_PORT}/sort", json=payload)
    return resp.json()


def main() -> None:
    proc = start_server()
    try:
        if not wait_for_server():
            print("Server failed to start. Output:")
            if proc.stdout:
                print(proc.stdout.read())
            return

        payload = {"values": [5, 2, 8, 1, 3, 7]}
        try:
            response = send_request(payload)
        except Exception as exc:
            response = {"error": str(exc)}
        print(f"{payload} -> {response}")
        output_file = response.get("output_file")
        if output_file:
            print(Path(output_file).read_text())
    finally:
        stop_process(proc)


if __name__ == "__main__":
    main()
