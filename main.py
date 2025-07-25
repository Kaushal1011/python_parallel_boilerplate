"""Generic entry point to launch FastAPI server and worker processes."""
import argparse
from boilerplate.manager import run_server


def main():
    parser = argparse.ArgumentParser(description="Launch API and workers")
    parser.add_argument(
        "-c",
        "--config",
        default="examples/merge_sort/config.json",
        help="Path to configuration JSON file",
    )
    args = parser.parse_args()
    run_server(args.config)


if __name__ == "__main__":
    main()
