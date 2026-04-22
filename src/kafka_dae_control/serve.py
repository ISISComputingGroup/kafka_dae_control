"""Main loop of the running IOC."""

import logging
from _socket import SocketType
from time import sleep

from kafka_dae_control.comms import read
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import RUNNING_REGISTER
from kafka_dae_control.run_state import RunRegister

logger = logging.getLogger(__name__)


def serve(sock: SocketType, data: "Data", ip: str) -> None:
    """Read the streaming control board parameters while the IOC is running.

    Args:
        sock: the socket to use for UDP comms.
        data: the dataclass for storing the state of the program
        ip: the IP of the streaming control board.

    Returns: None

    """
    while True:
        # Main loop here polls the vxi control board for statuses and updates the main data class
        try:
            i = read(sock, ip, RUNNING_REGISTER.address, RUNNING_REGISTER.size)
            if i is not None:
                data.running.value = i & RunRegister.STATUS_RUNNING != 0
        except TimeoutError:
            logger.error("Timeout reading from hardware")

        sleep(1)
