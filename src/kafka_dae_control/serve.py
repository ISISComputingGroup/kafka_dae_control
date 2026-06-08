"""Main loop of the running IOC."""

import logging
import socket
import threading
from functools import partial
from queue import Queue

from confluent_kafka import Producer
from p4p.server import Server

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.pvs.camonitor_callbacks import update_blocks
from kafka_dae_control.pvs.static_pvs import static_pv_provider
from kafka_dae_control.save_restore import load_data
from kafka_dae_control.threads.hardware_polling_thread import hardware_poll_thread
from kafka_dae_control.threads.update_pvs_thread import update_pvs_thread
from kafka_dae_control.worker_event import SetIPEvent, process_worker_event

# needed for p4p and pyepics to work together
try:
    import epicscorelibs.path.pyepics  # noqa: F401
except ImportError:  # pragma: no cover
    pass

from epics import camonitor

logger = logging.getLogger(__name__)


def serve(config: ControlConfig) -> None:
    """Read the streaming control board parameters while the IOC is running.

    Args:
        config: Configuration options.

    Returns: None

    """
    queue = Queue(maxsize=0)
    queue.put(SetIPEvent())

    data = load_data(config.state_file)
    static_pvs, static_provider = static_pv_provider(config.pv_prefix, data, queue)

    server = Server(providers=[static_provider])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock_lock = threading.RLock()

    # Start the hardware polling thread
    threading.Thread(
        target=hardware_poll_thread,
        args=(config, queue, sock, sock_lock),
        daemon=True,
        name="HardwarePoll",
    ).start()

    # Start the PV posts thread
    threading.Thread(
        target=update_pvs_thread, args=(static_pvs, data, config), daemon=True, name="UpdatePVs"
    ).start()
    producer = Producer(config.kafka_producer)

    # Start the camonitor thread. Note that the thread name is "Dummy-1"
    camonitor(
        f"{config.pv_prefix}CS:BLOCKSERVER:BLOCKNAMES",
        callback=partial(update_blocks, queue, config.pv_prefix),
    )

    # Start the p4p thread pool.
    with server:
        while True:
            # This is the main worker thread.
            event = queue.get(block=True)
            process_worker_event(event, config, data, producer, sock, sock_lock)
