import argparse
import sys

from d2s_admin.createsuperuser import add_parser as add_createsuperuser_parser
from d2s_admin.quickstart import add_parser as add_quickstart_parser


def main():
    parser = argparse.ArgumentParser(
        prog="d2s_admin",
        description="D2S administration tools",
    )
    subparsers = parser.add_subparsers(dest="command")

    add_quickstart_parser(subparsers)
    add_createsuperuser_parser(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
