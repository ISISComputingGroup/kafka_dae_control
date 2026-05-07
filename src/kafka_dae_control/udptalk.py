"""udptalk - debugging tool to read/write arbitrary data to/from a udp server.

This uses the same communication methods as the IOC.
"""

import argparse
import ipaddress
import logging
import socket

from kafka_dae_control.comms import read, write
from kafka_dae_control.defaults import READ_PORT, WRITE_PORT

logger = logging.getLogger(__name__)


def main() -> None:
    """UDPtalk debugging tool."""
    arg_parser = argparse.ArgumentParser(
        prog="udptalk",
        description="debugging tool to read/write arbitrary data to/from a udp device.",
    )

    subparser = arg_parser.add_subparsers(dest="command", required=True)

    common_subparser = argparse.ArgumentParser(add_help=False)

    common_subparser.add_argument("host", type=ipaddress.IPv4Address)
    common_subparser.add_argument("address", type=lambda x: int(x, 0))
    common_subparser.add_argument("--write-port", type=int, default=WRITE_PORT, required=False)
    common_subparser.add_argument("--read-port", type=int, default=READ_PORT, required=False)
    common_subparser.add_argument("--count", type=int, default=1)

    subparser.add_parser("read", help="read from register", parents=[common_subparser])

    write_subparser = subparser.add_parser(
        "write", help="write to register", parents=[common_subparser]
    )
    write_subparser.add_argument("data", type=lambda x: int(x, 0))

    args = arg_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if args.command == "read":
        read(sock, args.host, args.address, args.count)
    elif args.command == "write":
        write(sock, args.host, args.address, args.data, args.count)


if __name__ == "__main__":
    main()
