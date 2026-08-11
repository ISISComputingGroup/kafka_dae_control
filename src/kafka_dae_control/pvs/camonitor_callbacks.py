"""Utilities for parsing block values."""

import logging
from queue import PriorityQueue

from ibex_non_ca_helpers.compress_hex import dehex_decompress_and_dejson

from kafka_dae_control.queue_utils import QueueItem, QueuePriority
from kafka_dae_control.worker_event_types import BlocksUpdateEvent, RunControlUpdateEvent

logger = logging.getLogger(__name__)


def update_blocks(
    queue: PriorityQueue[QueueItem], prefix: str, *, char_value: str, **_: int
) -> None:
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


def run_control_update_callback(queue: PriorityQueue[QueueItem], *, value: int, **_: int) -> None:
    """Act on a run control PV update.

    Args:
        queue: The main queue on which to put events.
        value: The value of the PV.
        **_: Everything else.

    """
    logger.debug("run_control_update_callback: %s", value)
    queue.put(QueueItem(QueuePriority.HIGH, RunControlUpdateEvent(value=bool(value))))
