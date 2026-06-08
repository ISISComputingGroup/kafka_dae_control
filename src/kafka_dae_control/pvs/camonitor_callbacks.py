"""Utilities for parsing block values."""

import logging
from queue import Queue

from ibex_non_ca_helpers.compress_hex import dehex_decompress_and_dejson

from kafka_dae_control.worker_event import (
    BlocksUpdateEvent,
    WorkerEvent,
)

logger = logging.getLogger(__name__)


def update_blocks(queue: Queue[WorkerEvent], prefix: str, *, char_value: str, **_: int) -> None:
    """Update the list of blocks in the data class."""
    encoded_val = char_value.encode("utf-8")
    logger.debug("blocks_hexed: %s (char), %s (bytes)", char_value, encoded_val)
    blocks_unhexed = dehex_decompress_and_dejson(encoded_val)
    logger.debug("blocks_unhexed: %s", blocks_unhexed)
    queue.put(BlocksUpdateEvent(value=[f"{prefix}CS:SB:{x}" for x in blocks_unhexed]))
