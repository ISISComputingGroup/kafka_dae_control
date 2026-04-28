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
from kafka_dae_control.config import load_config
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import COMMS_REGISTER
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

    ap = argparse.ArgumentParser(description="KDAECTRL - Kafka-dae-control",
        epilog="This relies on EPICS environment variables. These are:"
        "\n\tEPICS_CA_ADDR_LIST: for the blockserver CA PVs"
        "\n\tEPICS_PVAS_INTF_ADDR_LIST: the interface to bind to for PVA",)
    ap.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config file.",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level)

    config = load_config(args.config)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # TODO anything after this point should be in serve really.

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
    static_provider = static_pv_provider(config.pv_prefix, data)

    server = Server(providers=[static_provider])
    producer = Producer({"bootstrap.servers": config.broker})

    camonitor(
        f"{config.pv_prefix}CS:BLOCKSERVER:BLOCKNAMES",
        callback=partial(update_blocks, config.pv_prefix, data),
    )

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    setup_hooks(data, producer, config.runinfo_topic, sock, config.board_ip)

    # "Handshake" and tell SCB to respond to our IP address.
    ip = ip_address(config.local_ip)
    ip_int = int.from_bytes(ip.packed, byteorder="big")
    print(f"IP IS {ip}, int repr is {ip_int}")
    write(sock, config.board_ip, COMMS_REGISTER.address, ip_int, COMMS_REGISTER.size)

    with server:
        # main loop
        serve(sock, data, config.board_ip)
