"""Serve command - starts the MediaTools API server for the web frontend."""

from __future__ import annotations

import argparse


def register_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the serve subcommand."""
    parser = subparsers.add_parser(
        "serve",
        help="Start the MediaTools API server",
        description="Starts an HTTP API server for the web frontend.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port to listen on (default: 7860)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)",
    )


def run(args: argparse.Namespace) -> int:
    """Run the serve command."""
    from mediatools.api_server import start_api_server

    port = args.port
    host = args.host

    print(f"Starting MediaTools API server on http://{host}:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        server = start_api_server(host=host, port=port)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        return 0
    except OSError as exc:
        if "Address already in use" in str(exc) or "Only one usage" in str(exc):
            print(f"Error: Port {port} is already in use")
            print("Try a different port with: mediatools serve --port <PORT>")
            return 1
        raise

    return 0
