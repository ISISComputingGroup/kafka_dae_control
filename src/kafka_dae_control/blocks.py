"""Utilities for parsing block values."""

import logging

from ibex_non_ca_helpers.compress_hex import dehex_decompress_and_dejson

from kafka_dae_control.data import Data

logger = logging.getLogger(__name__)


def update_blocks(prefix: str, data: "Data", *, char_value: str, **___: int) -> None:
    """Update the list of blocks in the data class."""
    encoded_val = char_value.encode("utf-8")
    logger.debug("blocks_hexed: %s (char), %s (bytes)", char_value, encoded_val)
    blocks_unhexed = dehex_decompress_and_dejson(encoded_val)
    logger.debug("blocks_unhexed: %s", blocks_unhexed)
    data.blocks = [f"{prefix}CS:SB:{x}" for x in blocks_unhexed]
