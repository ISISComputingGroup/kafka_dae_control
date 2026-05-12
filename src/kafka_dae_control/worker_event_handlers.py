"""Handlers called by the worker thread."""

import logging
import socket
import threading
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from confluent_kafka import Producer
from streaming_data_types import serialise_6s4t, serialise_pl72

from kafka_dae_control.comms import write_and_inv_then_verify, write_verify
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import RUNNING_REGISTER, RunRegister
from kafka_dae_control.run_start_nexus_structure import generate_nexus_structure
from kafka_dae_control.save_restore import save_file

logger = logging.getLogger(__name__)


def handle_begin(  # noqa: PLR0913, PLR0917
    config: ControlConfig,
    data: Data,
    producer: Producer,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: threading.Event,
) -> None:
    """Handle a begin command.

    Args:
        config: the program's configuration.
        data: the data class containing the state of the program.
        producer: the Kafka producer.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete

    """
    data.job_id = str(uuid.uuid4())
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                RUNNING_REGISTER.address,
                RunRegister.ETHERNET_OVERRIDE
                | RunRegister.RUN_SIGNAL_ETH
                | RunRegister.STREAM_EMPTY_FRAMES,
                RUNNING_REGISTER.size,
                verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
            )
    except Exception:
        # write has failed - go back to previous state
        logger.exception("Failed to start run: ")
        return

    blob = serialise_pl72(
        job_id=data.job_id,
        filename=f"{data.instrument_name}{data.run_number}.nxs",
        start_time=datetime.now(ZoneInfo("Europe/London")),
        run_name=str(data.run_number),
        nexus_structure=generate_nexus_structure(data),
        instrument_name=data.instrument_name,
        control_topic=config.runinfo_topic,
    )
    producer.produce(config.runinfo_topic, blob)
    producer.flush()
    logger.info("sent run start to %s", config.runinfo_topic)
    save_file(data, state_file=config.state_file)
    done_event.set()


def handle_end(  # noqa: PLR0913, PLR0917
    config: ControlConfig,
    data: Data,
    producer: Producer,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: threading.Event,
) -> None:
    """Handle an end command.

    Args:
        config: The program's configuration.
        data: the data class containing the state of the program.
        producer: the Kafka producer.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete

    """
    try:
        with sock_lock:
            # clear the ethernet override bit.
            write_and_inv_then_verify(
                config,
                sock,
                RUNNING_REGISTER.address,
                RunRegister.ETHERNET_OVERRIDE,
                RUNNING_REGISTER.size,
                verify=lambda x: x & RunRegister.STATUS_RUNNING == 0,
            )
    except Exception:
        # write has failed - go back to previous state
        logger.exception("Failed to end run: ")
        return
    blob = serialise_6s4t(job_id=data.job_id, stop_time=datetime.now(ZoneInfo("Europe/London")))
    producer.produce(config.runinfo_topic, blob)
    producer.flush()
    logger.info("sent run stop to %s", config.runinfo_topic)
    data.run_number += 1
    save_file(data, state_file=config.state_file)
    done_event.set()
