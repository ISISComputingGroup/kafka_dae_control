"""The main entrypoint for the KDAECTRL IOC."""

import argparse
import logging
import os
import socket
from functools import partial
from ipaddress import ip_address

from confluent_kafka import Producer
from p4p.server import Server

from kafka_dae_control.blocks import update_blocks
from kafka_dae_control.comms import write
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import COMMS_REGISTER, READ_PORT, WRITE_PORT
from kafka_dae_control.hooks import setup_hooks
from kafka_dae_control.save_restore import load_file
from kafka_dae_control.serve import serve
from kafka_dae_control.static_pvs import static_pv_provider

# needed for p4p and pyepics to work together
try:
    import epicscorelibs.path.pyepics  # noqa: F401
except ImportError:
    pass
import sys

from epics import camonitor

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the IOC."""
    if "EPICS_CA_ADDR_LIST" not in os.environ:
        logger.error("EPICS_CA_ADDR_LIST not set")
        sys.exit(1)
    if "EPICS_PVAS_INTF_ADDR_LIST" not in os.environ:
        logger.error("EPICS_PVAS_INTF_ADDR_LIST not set")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="KDAECTRL - Kafka-dae-control",
        epilog="This relies on EPICS environment variables. These are:"
        "\n\tEPICS_CA_ADDR_LIST: for the blockserver CA PVs"
        "\n\tEPICS_PVAS_INTF_ADDR_LIST: the interface to bind to for PVA",
    )
    parser.add_argument(
        "-i", "--ip", type=str, help="VXI streaming control board IP", required=True
    )
    parser.add_argument("--write-port", type=int, help="VXI SCB write port", default=WRITE_PORT)
    parser.add_argument("--read-port", type=int, help="VXI SCB read port", default=READ_PORT)

    parser.add_argument(
        "-p",
        "--pv-prefix",
        type=str,
        help="PV Prefix including IOC name and trailing colon.",
        required=True,
    )

    parser.add_argument(
        "-b", "--broker", type=str, help="Broker IP or hostname with port", required=True
    )
    parser.add_argument(
        "-r",
        "--topic",
        type=str,
        help="run info topic name",
        default=f"{socket.gethostname()}_runInfo",
    )
    parser.add_argument(
        "-l",
        "--local-ip",
        type=str,
        help="IP address of machine running IOC, required for setting comms register",
        required=True,
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG)

    loaded_data = load_file()

    title = loaded_data.get("title")
    users = loaded_data.get("users")
    # TODO need to load in:
    # job_id
    # run number
    #

    if not title:
        logger.warning("No title found in save file, defaulting to ''")
    if not users:
        logger.warning("No users found in save file, defaulting to ''")

    data = Data(
        title=title,
        users=users,
    )
    static_provider = static_pv_provider(args.pv_prefix, data)

    server = Server(providers=[static_provider])
    producer = Producer({"bootstrap.servers": args.broker})

    camonitor(
        f"{args.pv_prefix}CS:BLOCKSERVER:BLOCKNAMES",
        callback=partial(update_blocks, [args.pv_prefix, data]),
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    setup_hooks(data, producer, args.topic, sock, args.ip)

    # "Handshake" and tell SCB to respond to our IP address.
    ip = ip_address(args.local_ip)
    ip_int = int.from_bytes(ip.packed, byteorder="big")
    print(f"IP IS {ip}, int repr is {ip_int}")
    write(sock, args.ip, COMMS_REGISTER.address, ip_int, COMMS_REGISTER.size)

    with server:
        # main loop
        serve(sock, data, args.ip)
