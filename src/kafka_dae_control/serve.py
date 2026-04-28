"""Main loop of the running IOC."""

import logging
import socket
from functools import partial
from ipaddress import ip_address
from time import sleep

from confluent_kafka import Producer
from p4p.server import Server

from kafka_dae_control.blocks import update_blocks
from kafka_dae_control.comms import read, write_verify
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import COMMS_REGISTER, RUNNING_REGISTER
from kafka_dae_control.hooks import setup_hooks
from kafka_dae_control.run_state import RunRegister
from kafka_dae_control.save_restore import load_data
from kafka_dae_control.static_pvs import static_pv_provider

# needed for p4p and pyepics to work together
try:
    import epicscorelibs.path.pyepics  # noqa: F401
except ImportError:
    pass

from epics import camonitor

logger = logging.getLogger(__name__)


def serve(config: ControlConfig) -> None:
    """Read the streaming control board parameters while the IOC is running.

    Args:
        config: Configuration options.

    Returns: None

    """
    data = Data(**load_data())
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
    write_verify(
        sock,
        config.board_ip,
        COMMS_REGISTER.address,
        ip_int,
        COMMS_REGISTER.size,
        verify=lambda x: x == ip_int,
    )

    with server:
        # main loop

        while True:
            # Main loop here polls the vxi control board for statuses
            # and updates the main data class
            try:
                hw_running = read(
                    sock, config.board_ip, RUNNING_REGISTER.address, RUNNING_REGISTER.size
                )
                if hw_running is not None:
                    data.running.value = hw_running & RunRegister.STATUS_RUNNING != 0
            except TimeoutError:
                logger.error("Timeout reading from hardware")

            sleep(1)
