"""Module entry-point for python -m code_arena."""

from .cli import cli


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
