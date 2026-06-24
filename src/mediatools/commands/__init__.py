"""CLI command handlers.

Each module exports two functions:

- ``register_parser(subparsers)`` — registers the command's argparse subparser.
- ``run(args)`` — executes the command and returns an exit code.
"""
