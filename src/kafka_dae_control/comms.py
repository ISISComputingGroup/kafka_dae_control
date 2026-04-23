"""Utilities for communicating to a UDP device such as a streaming control board."""

import logging
import socket
from collections.abc import Callable
from time import sleep
from typing import TypeAlias

from kafka_dae_control.defaults import READ_PORT, RECEIVE_BUFFER_SIZE, WRITE_PORT

logger = logging.getLogger(__name__)

ATTEMPTS = 5
SLEEP_BETWEEN_ATTEMPTS_S = 0.1
SLEEP_AFTER_WRITE_S = 0.1

VerifyFunc: TypeAlias = Callable[[int], bool]


def write_verify(
    sock: socket.SocketType,
    host: str,
    address: int,
    new_value: int,
    count: int,
    verify: VerifyFunc | None = None,
) -> None:
    """Write a value then verify it by reading it back with a retry/timeout loop.

    Args:
        sock: the UDP socket instance
        host: the streaming control board host IP
        address: the address to write to
        new_value: the data to write
        count: the number of 32 bit words to write
        verify: Optionally verify against a different provided value by ORing it

    Returns: None

    """
    write(sock, host, address, new_value, count)
    # sleep after writing
    sleep(SLEEP_AFTER_WRITE_S)

    current_val = None
    # check to make sure read value is equal to the new (masked) value
    for _i in range(ATTEMPTS + 1):
        current_val = read(sock, host, address, count)
        if (verify is not None and not verify(current_val)) or current_val != new_value:
            sleep(SLEEP_BETWEEN_ATTEMPTS_S)
        else:
            return

    raise OSError(
        f"({host}) Could not write {count} 32 bit words to address {address} "
        f"(set data={new_value}, readback={current_val})"
    )


def write_and_inv_then_verify(
    sock: socket.SocketType,
    host: str,
    address: int,
    data: int,
    count: int,
    verify_against: VerifyFunc | None = None,
) -> None:
    """Write a value by masking the current value with an AND of the inverse new data then verify.

    This is essentially used to "clear" a bit.

    Args:
        sock: the UDP socket instance
        host: the streaming control board host IP
        address: the address to write to
        data: the data to write
        count: the number of 32 bit words to write
        verify_against: Optionally verify against a different provided value by ORing it

    Returns: None

    """
    # read current value
    current_val = read(sock, host, address, count)
    # AND mask it with the inverse of new data
    new_value = current_val & ~data
    # write the new value and verify
    write_verify(sock, host, address, new_value, count, verify_against)


def write_or_then_verify(
    sock: socket.SocketType,
    host: str,
    address: int,
    data: int,
    count: int,
    verify_against: VerifyFunc | None = None,
) -> None:
    """Write a value by masking it against the current value with an OR of the new data then verify.

    Args:
        sock: the UDP socket instance
        host: the streaming control board host IP
        address: the address to write to
        data: the data to write
        count: the number of 32 bit words to write
        verify_against: Optionally verify against a different provided value by ORing it

    Returns: None

    """
    # read current value
    current_val = read(sock, host, address, count)
    # OR mask it with the new data
    new_value = current_val | data
    # write the new value and verify
    write_verify(sock, host, address, new_value, count, verify_against)


def write(sock: socket.SocketType, host: str, address: int, data: int, count: int) -> None:
    """Write a value.

    Args:
        sock: the UDP socket instance
        host: the streaming control board host IP
        address: the address to write to
        data: the data to write
        count: the number of 32 bit words to write

    Returns: None

    """
    logger.debug(
        f"({host}) wrote {count} 32-bit words to address {address} (data={data}, bin: {data:b})"
    )
    # write request is 32-bit address, 16 bit block size and 32 bit data
    message = (
        address.to_bytes(length=4, byteorder="big")
        + count.to_bytes(length=2, byteorder="big")
        + data.to_bytes(length=4, byteorder="big")
    )
    sock.sendto(message, (host, WRITE_PORT))


def read(sock: socket.SocketType, host: str, address: int, count: int) -> int:
    """Read a register on the streaming control board and return its value.

    Args:
        sock: the UDP socket instance
        host: the IP address of the streaming control board
        address: the address to read
        count: how many 32 bit words to request when reading.

    Returns: The received data

    """
    logger.debug("(%s) requesting read %s 32-bit words from address %s", host, count, address)
    sock.settimeout(2.0)

    # request format is 32 bit address + 16 bit block size
    message = address.to_bytes(length=4, byteorder="big") + count.to_bytes(2, byteorder="big")

    sock.sendto(message, (host, READ_PORT))

    data, recv_address = sock.recvfrom(RECEIVE_BUFFER_SIZE)

    # parse the 32 bit address
    base_addr = int.from_bytes(data[:4], byteorder="big")
    if base_addr != address:
        logger.warning(
            "Received address (%s) not same as requested address (%s))", recv_address, address
        )
        return None

    # parse the 16 bit block size
    block_size = int.from_bytes(data[4:6], byteorder="big")

    # parse the 32 bit data. block size is in 32-bit words, so need to multiply by 4 here as 4*8 bytes is 32 bits.
    data = int.from_bytes(data[6 : 6 + (block_size * 4)], byteorder="big")
    logger.debug(
        f"Response: addr = {base_addr}, block size = {block_size}, data = {data} (bin: {data:b})"
    )
    return data
