"""Handlers called by the worker thread."""

import logging
import socket
import threading
import uuid
from datetime import datetime
from functools import partial
from zoneinfo import ZoneInfo

from confluent_kafka import KafkaError, Message, Producer
from streaming_data_types import serialise_6s4t, serialise_pl72

from kafka_dae_control.comms import write_and_inv_then_verify, write_verify
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import RUNNING_REGISTER, RunRegister
from kafka_dae_control.event_with_value import EventWithValue
from kafka_dae_control.run_start_nexus_structure import generate_nexus_structure
from kafka_dae_control.save_restore import save_file

logger = logging.getLogger(__name__)


def delivery_report_run_info(
    done_event: EventWithValue[None], err: KafkaError | None, msg: Message
) -> None:
    """Act on a Kafka delivery report.

    This is used for the run info messages to tell anything waiting on these that the message was
    either delivered or not.

    Args:
        done_event: The event to call set() or set exception depending on result.
        err: The exception given by Kafka
        msg: The message sent by Kafka.

    """
    logger.debug("Got callback for kafka message. err: %s, msg: %s", err, msg)
    if err is not None:
        error = f"Error with kafka delivery: {err.name()} ({err.str()})"
        logger.error(error)
        done_event.err = Exception(error)
    else:
        logger.debug("Setting the done event")
        done_event.set()


def handle_begin(  # noqa: PLR0913, PLR0917
    config: ControlConfig,
    data: Data,
    producer: Producer,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
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
    blob = serialise_pl72(
        job_id=data.job_id,
        filename=f"{data.instrument_name}{data.run_number}.nxs",
        start_time=datetime.now(ZoneInfo("Europe/London")),
        run_name=str(data.run_number),
        nexus_structure=generate_nexus_structure(data),
        instrument_name=data.instrument_name,
        control_topic=config.runinfo_topic,
    )
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
        producer.produce(
            config.runinfo_topic, blob, callback=partial(delivery_report_run_info, done_event)
        )
        producer.poll(0)
        logger.info("sent run start to %s", config.runinfo_topic)
        save_file(data, state_file=config.state_file)
    except Exception as e:
        logger.exception("Failed to start run: ")
        done_event.err = e
        return


def handle_end(  # noqa: PLR0913, PLR0917
    config: ControlConfig,
    data: Data,
    producer: Producer,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
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
    blob = serialise_6s4t(job_id=data.job_id, stop_time=datetime.now(ZoneInfo("Europe/London")))
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
        producer.produce(
            config.runinfo_topic, blob, callback=partial(delivery_report_run_info, done_event)
        )
        producer.poll(0)
        logger.info("sent run stop to %s", config.runinfo_topic)
        data.run_number += 1
        save_file(data, state_file=config.state_file)

    except Exception as e:
        logger.exception("Failed to end run: ")
        done_event.err = e
        return
