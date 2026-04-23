"""DAE run state enum and state machine."""

import logging
import typing
import uuid
from _socket import SocketType
from datetime import datetime
from enum import Enum, IntFlag
from zoneinfo import ZoneInfo

from confluent_kafka import Producer
from streaming_data_types import serialise_6s4t, serialise_pl72

from kafka_dae_control.comms import write_and_inv_then_verify, write_verify
from kafka_dae_control.defaults import RUNNING_REGISTER
from kafka_dae_control.run_start_nexus_structure import generate_nexus_structure

if typing.TYPE_CHECKING:
    from kafka_dae_control.data import Data

logger = logging.getLogger(__name__)


class RunState(Enum):
    """Enum for all DAE runstate states."""

    PROCESSING = 0  # not used
    SETUP = 1
    RUNNING = 2
    PAUSED = 3
    WAITING = 4  # not used
    VETOING = 5  # not used
    ENDING = 6
    SAVING = 7  # not used
    RESUMING = 8
    PAUSING = 9
    BEGINNING = 10
    ABORTING = 11  # not used
    UPDATING = 12  # not used
    STORING = 13  # not used
    CHANGING = 14  # not used


class RunRegister(IntFlag):
    """Enum for bits in the run register."""

    ETHERNET_OVERRIDE = 0x01
    RUN_SIGNAL_ETH = 0x02
    RUN_SIGNAL_VXI = 0x04
    NO_FRAME_INC = 0x08
    STREAM_EMPTY_FRAMES = 0x10
    STATUS_RUNNING = 0x20


def on_run_state_change(  # noqa: PLR0913, PLR0917
    data: "Data",
    producer: Producer,
    run_info_topic: str,
    sock: SocketType,
    host: str,
    old_value: bool,
    new_value: bool,
) -> None:
    """React to a run state change.

    Args:
        data: The data class containing the state of the program
        producer: The Kafka producer object
        run_info_topic: The run info topic to push to
        sock: the UDP socket instance
        host: the streaming control board host IP
        old_value: the old run state value
        new_value: the new run state value

    Returns: None

    """
    logger.debug("run state value changed from %s to %s", old_value, new_value)

    if new_value == RunState.BEGINNING:
        data.job_id.value = str(uuid.uuid4())
        try:
            write_verify(
                sock,
                host,
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
            data.run_state.value = old_value
            return
        blob = serialise_pl72(
            job_id=data.job_id.value,
            filename=f"{data.instrument_name}{data.run_number}.nxs",
            start_time=datetime.now(ZoneInfo("Europe/London")),
            run_name=str(data.run_number.value),
            nexus_structure=generate_nexus_structure(data),
            instrument_name=data.instrument_name,
            control_topic=run_info_topic,
        )
        producer.produce(run_info_topic, blob)
        logger.info("sent run start to %s", run_info_topic)
        producer.flush()
        data.run_state.value = RunState.RUNNING
    elif new_value == RunState.ENDING:
        try:
            # clear the ethernet override bit.
            write_and_inv_then_verify(
                sock,
                host,
                RUNNING_REGISTER.address,
                RunRegister.ETHERNET_OVERRIDE,
                RUNNING_REGISTER.size,
                verify_against=lambda x: x & RunRegister.STATUS_RUNNING == 0,
            )
        except Exception:
            # write has failed - go back to previous state
            logger.exception("Failed to end run: ")
            data.run_state.value = old_value
            return
        blob = serialise_6s4t(
            job_id=data.job_id.value, stop_time=datetime.now(ZoneInfo("Europe/London"))
        )
        producer.produce(run_info_topic, blob)
        logger.info("sent run stop to %s", run_info_topic)
        producer.flush()
        data.run_state.value = RunState.SETUP
        data.run_number.value += 1
    elif new_value == RunState.PAUSING:
        # TODO write to hardware, but don't send run stop
        pass
    elif new_value == RunState.RESUMING:
        # TODO write to hardware but don't send run start
        pass
    else:
        logger.debug(
            "Got other run state (%s) but not acting on it. Old/current value: %s",
            new_value,
            old_value,
        )
