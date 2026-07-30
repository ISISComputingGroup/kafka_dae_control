"""Utilities for parsing block values."""

import logging
from queue import Queue

from ibex_non_ca_helpers.compress_hex import dehex_decompress_and_dejson

from kafka_dae_control.queue_utils import QueueItem, QueuePriority
from kafka_dae_control.worker_event_types import BlocksUpdateEvent, WorkerEvent

logger = logging.getLogger(__name__)


def update_blocks(queue: Queue[WorkerEvent], prefix: str, *, char_value: str, **_: int) -> None:
    """Update the list of blocks in the data class."""
    encoded_val = char_value.encode("utf-8")
    logger.debug("blocks_hexed: %s (char), %s (bytes)", char_value, encoded_val)
    blocks_unhexed = dehex_decompress_and_dejson(encoded_val)
    logger.debug("blocks_unhexed: %s", blocks_unhexed)
    queue.put(
        QueueItem(
            QueuePriority.LOW,
            BlocksUpdateEvent(value=[f"{prefix}CS:SB:{x}" for x in blocks_unhexed]),
        )
    )


def run_control_update_callback(queue: Queue[WorkerEvent], *, value: int, **_: int) -> None:
    """Act on a run control PV update.

    Args:
        queue: The main queue on which to put events.
        value: The value of the PV.
        **_: Everything else.

    """
    # todo check that value is actually an int
    # todo push an update to the queue immediately
    pass
