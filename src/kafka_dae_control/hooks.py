"""Setup hooks for reacting to PV updates."""

import logging
from functools import partial
from socket import SocketType

from confluent_kafka import Producer

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.run_state import on_run_state_change
from kafka_dae_control.save_restore import save_file

logger = logging.getLogger(__name__)


def setup_hooks(
    data: "Data",
    producer: Producer,
    config: ControlConfig,
    sock: SocketType,
) -> None:
    """Set up hooks used for reacting to a PV update.

    Args:
        data: The data class containing the state of the application.
        producer: The Kafka producer instance.
        config: The program's configuration.
        sock: The socket used for UDP communication.

    Returns: None

    """
    logger.info("setting up hooks")
    data.run_state.attach(
        partial(on_run_state_change, data, producer, config.runinfo_topic, sock, config.board_ip)
    )

    # save-restore file updating
    data.title.attach(partial(save_file, data, state_file=config.state_file))
    data.users.attach(partial(save_file, data, state_file=config.state_file))
    data.run_number.attach(partial(save_file, data, state_file=config.state_file))
    data.job_id.attach(partial(save_file, data, state_file=config.state_file))
