"""Setup hooks for reacting to PV updates."""

import logging
from socket import SocketType
from functools import partial

from confluent_kafka import Producer

from kafka_dae_control.data import Data
from kafka_dae_control.run_state import on_run_state_change
from kafka_dae_control.save_restore import save_file

logger = logging.getLogger(__name__)


def setup_hooks(
    data: "Data", producer: Producer, run_info_topic: str, sock: SocketType, host: str
) -> None:
    """Set up hooks used for reacting to a PV update.

    Args:
        data: The data class containing the state of the application.
        producer: The Kafka producer instance.
        run_info_topic: The topic to push run info updates to.
        sock: The socket used for UDP communication.
        host: the streaming control board IP address.

    Returns: None

    """
    logger.info("setting up hooks")
    data.run_state.attach(partial(on_run_state_change, data, producer, run_info_topic, sock, host))

    # save-restore file updating
    data.title.attach(partial(save_file, data))
    data.users.attach(partial(save_file, data))
    data.run_number.attach(partial(save_file, data))
    data.job_id.attach(partial(save_file, data))
