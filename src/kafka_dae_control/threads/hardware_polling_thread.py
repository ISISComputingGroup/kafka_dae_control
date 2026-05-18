"""Thread for polling the hardware and sending updates to the worker thread's queue."""

import logging
import socket
import threading
from queue import Queue
from time import sleep
from typing import Never

from kafka_dae_control.comms import read
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import RUNNING_REGISTER, RunRegister
from kafka_dae_control.worker_event import HardwareUpdate, HardwareUpdateEvent, WorkerEvent

logger = logging.getLogger(__name__)


def hardware_poll_thread(
    config: ControlConfig,
    queue: Queue[WorkerEvent],
    sock: socket.SocketType,
    sock_lock: threading.RLock,
) -> Never:
    """Thread for polling the hardware and sending updates to the worker thread's queue.

    Args:
        config: the program's configuration
        queue: the worker thread queue to add updates to after polling hardware
        sock: the socket instance
        sock_lock: the lock to use when using the socket instance

    """
    while True:
        try:
            with sock_lock:
                running_register_readback = read(
                    sock,
                    config.board_ip,
                    RUNNING_REGISTER.address,
                    RUNNING_REGISTER.size,
                    config.read_port,
                )

            queue.put(
                HardwareUpdateEvent(
                    HardwareUpdate(
                        hw_running=running_register_readback & RunRegister.STATUS_RUNNING != 0
                    )
                )
            )

        except Exception:
            logger.exception("Error occurred when polling hardware: ")

        sleep(config.poll_interval_s)
