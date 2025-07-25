from multiprocessing import Value, Lock
from boilerplate.manager import run_server


def main():
    counter = Value('i', 0)
    lock = Lock()
    shared = {"counter": counter, "counter_lock": lock}
    run_server("examples/round_robin/config.json", shared_objects=shared)


if __name__ == "__main__":
    main()
