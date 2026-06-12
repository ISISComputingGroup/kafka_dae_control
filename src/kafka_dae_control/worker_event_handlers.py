"""Handlers called by the worker thread."""

import logging
import socket
import threading
import uuid
from datetime import datetime
from functools import partial
from queue import Queue
from zoneinfo import ZoneInfo

from confluent_kafka import KafkaError, Message, Producer
from streaming_data_types import serialise_6s4t, serialise_pl72

from kafka_dae_control.comms import write_and_inv_then_verify, write_verify
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import (
    FrameSyncSelect,
    PeriodMode,
    Registers,
    RunRegister,
)
from kafka_dae_control.event_with_value import EventWithValue
from kafka_dae_control.run_start_nexus_structure import generate_nexus_structure
from kafka_dae_control.save_restore import save_file
from kafka_dae_control.threads.hardware_polling_thread import poll_hardware
from kafka_dae_control.worker_event_types import WorkerEvent

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
    queue: Queue[WorkerEvent],
) -> None:
    """Handle a begin command.

    Args:
        config: the program's configuration.
        data: the data class containing the state of the program.
        producer: the Kafka producer.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete
        queue: The queue to put hardware polling updates on after beginning

    """
    if data.running:
        e = OSError("The hardware is already running - doing nothing")
        logger.error(e)
        done_event.err = e
        return
    data.job_id = str(uuid.uuid4())
    run_name = f"{config.instrument_name}{data.run_number}"
    blob = serialise_pl72(
        job_id=data.job_id,
        filename=f"{run_name}.nxs",
        start_time=datetime.now(ZoneInfo("Europe/London")),
        run_name=run_name,
        nexus_structure=generate_nexus_structure(config, data),
        instrument_name=config.instrument_name,
        control_topic=config.runinfo_topic,
    )
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                address=config.register_map[Registers.RUNNING_REGISTER],
                data=RunRegister.ETHERNET_OVERRIDE
                | RunRegister.RUN_SIGNAL_ETH
                | RunRegister.STREAM_EMPTY_FRAMES,
                verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
            )
        producer.produce(
            config.runinfo_topic, blob, callback=partial(delivery_report_run_info, done_event)
        )
        producer.flush(timeout=config.flush_timeout_s)
        logger.info("sent run start to %s", config.runinfo_topic)
        save_file(data, state_file=config.state_file)
        # immediately poll hardware to avoid being able to begin again before hardware is updated
        poll_hardware(config, queue, sock, sock_lock)
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
    queue: Queue[WorkerEvent],
) -> None:
    """Handle an end command.

    Args:
        config: The program's configuration.
        data: the data class containing the state of the program.
        producer: the Kafka producer.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete
        queue: The queue to put hardware polling updates on after ending

    """
    if not data.running:
        e = OSError("The hardware is already not running - doing nothing")
        logger.error(e)
        done_event.err = e
        return
    blob = serialise_6s4t(job_id=data.job_id, stop_time=datetime.now(ZoneInfo("Europe/London")))
    try:
        with sock_lock:
            # clear the ethernet override bit.
            write_and_inv_then_verify(
                config,
                sock,
                address=config.register_map[Registers.RUNNING_REGISTER],
                data=RunRegister.ETHERNET_OVERRIDE,
                verify=lambda x: x & RunRegister.STATUS_RUNNING == 0,
            )
        producer.produce(
            config.runinfo_topic, blob, callback=partial(delivery_report_run_info, done_event)
        )
        producer.flush(timeout=config.flush_timeout_s)
        logger.info("sent run stop to %s", config.runinfo_topic)
        data.run_number += 1
        save_file(data, state_file=config.state_file)
        # immediately poll hardware to avoid being able to end again before hardware is updated
        poll_hardware(config, queue, sock, sock_lock)
    except Exception as e:
        logger.exception("Failed to end run: ")
        done_event.err = e
        return


def handle_frame_sync_sp_change(  # noqa: PLR0913, PLR0917
    value: FrameSyncSelect,
    config: ControlConfig,
    data: Data,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
) -> None:
    """Handle a frame sync select setpoint change.

    Args:
        value: the new value to write to hardware
        config: The program's configuration.
        data: the data class containing the state of the program.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete

    """
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                address=config.register_map[Registers.FRAME_SYNC_SEL_REGISTER],
                data=value.value,
                verify=lambda x: x == value.value,
            )
    except Exception as e:
        logger.exception("Failed to set frame sync select: ")
        done_event.err = e
        return
    data.frame_sync_select_sp = value
    done_event.set()


def set_num_periods(  # noqa: PLR0913, PLR0917
    value: int,
    config: ControlConfig,
    data: Data,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
) -> None:
    """Set the number of periods on the hardware.

    Args:
        value: the new value to write to hardware
        config: The program's configuration.
        data: the data class containing the state of the program.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete


    """
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                address=config.register_map[Registers.PERIOD_NUMBER_LIMIT],
                data=value,
                verify=lambda x: x == value,
            )
    except Exception as e:
        logger.exception("Failed to set num periods: ")
        done_event.err = e
        return
    data.num_periods_sp = value
    done_event.set()


def set_current_period(  # noqa: PLR0913, PLR0917
    value: int,
    config: ControlConfig,
    data: Data,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
) -> None:
    """Set the current period number on the hardware.

    Args:
        value: the new value to write to hardware
        config: The program's configuration.
        data: the data class containing the state of the program.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete

    """
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                address=config.register_map[Registers.PERIOD_COMP_CURRENT],
                data=value,
                verify=lambda x: x == value,
            )
    except Exception as e:
        logger.exception("Failed to set current period: ")
        done_event.err = e
        return
    data.current_period_sp = value
    done_event.set()


def set_period_mode(  # noqa: PLR0913, PLR0917
    value: PeriodMode,
    config: ControlConfig,
    data: Data,
    sock: socket.SocketType,
    sock_lock: threading.RLock,
    done_event: EventWithValue[None],
) -> None:
    """Set the period mode on the hardware.

    Args:
        value: the new value to write to hardware
        config: The program's configuration.
        data: the data class containing the state of the program.
        sock: the socket instance.
        sock_lock: the lock to acquire when using the socket instance.
        done_event: The event to call set() on when complete

    """
    # todo set the two toggles as we're write_verifying here
    try:
        with sock_lock:
            write_verify(
                config,
                sock,
                address=config.register_map[Registers.PERIOD_CONTROL],
                data=value.value,
                verify=lambda x: x == value.value,
            )
    except Exception as e:
        logger.exception("Failed to set current period: ")
        done_event.err = e
        return
    data.current_period_sp = value
    done_event.set()
