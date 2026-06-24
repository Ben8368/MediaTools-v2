"""Allow running MediaTools with `python -m mediatools`."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
