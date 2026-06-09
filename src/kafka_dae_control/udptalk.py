"""udptalk - debugging tool to read/write arbitrary data to/from a udp server.

This uses the same communication methods as the IOC.
"""

import argparse
import ipaddress
import logging
import socket

from kafka_dae_control.comms import read, write
from kafka_dae_control.defaults import READ_PORT, REGISTER_SIZE_WORDS, WRITE_PORT

logger = logging.getLogger(__name__)


def main() -> None:
    """UDPtalk debugging tool."""
    arg_parser = argparse.ArgumentParser(
        prog="udptalk",
        description="Debugging tool to read/write arbitrary data to/from a streaming control board",
        epilog="""This uses the same communication methods as the IOC and can be used to send and receive data to/from the device, counted by the number of 32-bit words.

For example:
    `udptalk read 192.168.1.100 0x0 --count 1` will read 1 32-bit word from the 0x0 register from 192.168.1.100.
    `udptalk write 192.168.1.100 0x0 0x13` will write 0x13 to the 0x0 register on 192.168.1.100.
""",  # noqa: E501
        formatter_class=argparse.RawTextHelpFormatter,
    )

    subparser = arg_parser.add_subparsers(dest="command", required=True)

    common_subparser = argparse.ArgumentParser(add_help=False)

    common_subparser.add_argument("host", type=ipaddress.IPv4Address, help="IP address of device")
    common_subparser.add_argument(
        "address", type=lambda x: int(x, 0), help="Register address, in int or hex format"
    )
    common_subparser.add_argument(
        "--count", type=int, default=REGISTER_SIZE_WORDS, help="number of words to read/write"
    )

    read_subparser = subparser.add_parser(
        "read", help="read from register", parents=[common_subparser]
    )
    read_subparser.add_argument(
        "-p",
        "--port",
        type=int,
        default=READ_PORT,
        required=False,
        help="Port to use when reading from device",
    )

    write_subparser = subparser.add_parser(
        "write", help="write to register", parents=[common_subparser]
    )
    write_subparser.add_argument(
        "-p",
        "--port",
        default=WRITE_PORT,
        required=False,
        help="Port to use when writing to device",
    )
    write_subparser.add_argument(
        "data", type=lambda x: int(x, 0), help="data to write, in either int or hex format"
    )

    args = arg_parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    if args.command == "read":
        read(sock, args.host, address=args.address, count=args.count, port=args.port)
    elif args.command == "write":
        write(
            sock, args.host, address=args.address, data=args.data, count=args.count, port=args.port
        )


if __name__ == "__main__":
    main()
