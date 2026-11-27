"""Utilities for emulating the streaming control board."""


def _be_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big")


def _be_words(b: bytes) -> list[int]:
    return [int.from_bytes(b[i : i + 4], byteorder="big") for i in range(0, len(b), 4)]
