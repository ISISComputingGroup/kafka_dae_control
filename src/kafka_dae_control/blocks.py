"""Utilities for parsing block values."""

import logging

from ibex_non_ca_helpers.compress_hex import dehex_decompress_and_dejson

from kafka_dae_control.data import Data

logger = logging.getLogger(__name__)


def update_blocks(
    prefix: str, data: "Data", *, value: bytes, char_value: str, **___: int
) -> None:
    """Update the list of blocks in the data class."""
    logger.debug("blocks_hexed: %s (char), %s (str)", char_value, value)
    blocks_unhexed = dehex_decompress_and_dejson(value)
    logger.debug("blocks_unhexed: %s", blocks_unhexed)
    data.blocks = [f"{prefix}CS:SB:{x}" for x in blocks_unhexed]
