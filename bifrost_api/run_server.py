"""Run Bifrost API server."""

import argparse
import os
import sys

import uvicorn


def main():
    """Run the Bifrost API server."""
    parser = argparse.ArgumentParser(description="Run Bifrost API server")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1)",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)",
    )

    args = parser.parse_args()

    # Configure server
    config = {
        "app": "bifrost_api.app:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "reload": args.reload,
        "workers": args.workers if not args.reload else 1,  # Workers incompatible with reload
    }

    print(f"Starting Bifrost API server on {args.host}:{args.port}")
    print(f"Workers: {config['workers']}")
    print(f"Reload: {args.reload}")
    print(f"Log level: {args.log_level}")
    print()

    # Run server
    uvicorn.run(**config)


if __name__ == "__main__":
    main()
