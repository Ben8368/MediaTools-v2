#!/usr/bin/env python3
"""Start the local MediaTools API and light frontend.

This script is intentionally Python-only so Windows, macOS, and Linux can use
the same startup entry:

    python scripts/start.py
"""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_API_PORT = 7860
DEFAULT_FRONTEND_HOST = "127.0.0.1"
DEFAULT_FRONTEND_PORT = 5173


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/start.py",
        description="Start the MediaTools local API and frontend.",
    )
    parser.add_argument("--api-host", default=DEFAULT_API_HOST, help="API host to bind.")
    parser.add_argument("--api-port", type=int, default=DEFAULT_API_PORT, help="API port.")
    parser.add_argument(
        "--frontend-host",
        default=DEFAULT_FRONTEND_HOST,
        help="Frontend dev server host.",
    )
    parser.add_argument(
        "--frontend-port",
        type=int,
        default=DEFAULT_FRONTEND_PORT,
        help="Frontend dev server port.",
    )
    parser.add_argument(
        "--backend-only",
        action="store_true",
        help="Only start the Python API server.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Do not run npm ci/install before starting the frontend.",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the frontend URL in the default browser.",
    )
    return parser


def _merged_env(api_host: str, api_port: int) -> dict[str, str]:
    env = os.environ.copy()
    src_path = str(ROOT / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src_path if not existing else os.pathsep.join([src_path, existing])
    env["VITE_MEDIATOOLS_API_TARGET"] = f"http://{api_host}:{api_port}"
    return env


def _npm_executable() -> str:
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm and os.name == "nt":
        npm = shutil.which("npm")
    if not npm:
        raise RuntimeError(
            "npm was not found on PATH. Install Node.js 20+ or run with --backend-only.",
        )
    return npm


def _run_frontend_install(npm: str, env: dict[str, str]) -> None:
    node_modules = FRONTEND_DIR / "node_modules"
    if node_modules.exists():
        return
    command = [npm, "ci"] if (FRONTEND_DIR / "package-lock.json").exists() else [npm, "install"]
    print(f"[start] Installing frontend dependencies: {' '.join(command)}", flush=True)
    result = subprocess.run(command, cwd=FRONTEND_DIR, env=env, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Frontend dependency install failed with exit code {result.returncode}.",
        )


def _terminate(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=8)
    except subprocess.TimeoutExpired:
        process.kill()


def _start_processes(args: argparse.Namespace) -> list[subprocess.Popen[object]]:
    env = _merged_env(args.api_host, args.api_port)
    processes: list[subprocess.Popen[object]] = []
    try:
        api_command = [
            sys.executable,
            "-m",
            "mediatools",
            "serve",
            "--host",
            args.api_host,
            "--port",
            str(args.api_port),
        ]
        print(f"[start] API: {' '.join(api_command)}", flush=True)
        processes.append(subprocess.Popen(api_command, cwd=ROOT, env=env))

        if args.backend_only:
            return processes

        if not FRONTEND_DIR.exists():
            raise RuntimeError(
                "frontend/ does not exist; use --backend-only to start only the API.",
            )

        npm = _npm_executable()
        if not args.no_install:
            _run_frontend_install(npm, env)

        frontend_command = [
            npm,
            "run",
            "dev",
            "--",
            "--host",
            args.frontend_host,
            "--port",
            str(args.frontend_port),
        ]
        print(f"[start] Frontend: {' '.join(frontend_command)}", flush=True)
        processes.append(subprocess.Popen(frontend_command, cwd=FRONTEND_DIR, env=env))
        return processes
    except Exception:
        for process in reversed(processes):
            _terminate(process)
        raise


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    frontend_url = f"http://{args.frontend_host}:{args.frontend_port}"
    api_url = f"http://{args.api_host}:{args.api_port}"
    processes: list[subprocess.Popen[object]] = []

    try:
        processes = _start_processes(args)
        print(f"[start] API URL: {api_url}", flush=True)
        if not args.backend_only:
            print(f"[start] Frontend URL: {frontend_url}", flush=True)
            if args.open:
                time.sleep(1)
                webbrowser.open(frontend_url)
        print("[start] Press Ctrl+C to stop all processes.", flush=True)

        while True:
            for process in processes:
                code = process.poll()
                if code is not None:
                    print(f"[start] A child process exited with code {code}.", flush=True)
                    return int(code)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[start] Stopping MediaTools...", flush=True)
        return 0
    except RuntimeError as exc:
        print(f"[start] Error: {exc}", file=sys.stderr, flush=True)
        return 1
    finally:
        for process in reversed(processes):
            _terminate(process)


if __name__ == "__main__":
    if os.name != "nt":
        signal.signal(signal.SIGTERM, lambda _signum, _frame: sys.exit(0))
    raise SystemExit(main())
