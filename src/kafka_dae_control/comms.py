"""Utilities for communicating to a UDP device such as a streaming control board.

The functions in this module assume that they have exclusive use of the passed-in socket.
This means that the socket object should be protected by a lock, external to this module.
"""

import ipaddress
import logging
import socket
import threading
from collections.abc import Callable
from ipaddress import ip_address
from time import sleep

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import COMMS_REGISTER, RECEIVE_BUFFER_SIZE

logger = logging.getLogger(__name__)

WRITE_ATTEMPTS = 3
VERIFY_ATTEMPTS = 5
SLEEP_BETWEEN_VERIFY_ATTEMPTS_S = 0.1
SLEEP_AFTER_WRITE_S = 0.1

type VerifyFunc = Callable[[int], bool]


def write_and_inv_then_verify(  # noqa: PLR0913 PLR0917
    config: ControlConfig,
    sock: socket.SocketType,
    address: int,
    data: int,
    count: int,
    verify: VerifyFunc,
    write_attempts: int = WRITE_ATTEMPTS,
) -> None:
    """Write by reading the current value then ANDing it with the inverse of the new data.

    This is essentially used to "clear" a bit and call :func:`write_verify`

    An example could be you want to clear bit `0x1`(binary: 01). `0x3` (binary: 11) is
    the current value, so you AND `0x3` (binary: 11)
    with `0x2` (binary: 10) (as this is the inverse of `0x1`(binary: 01))
    then verify that you end up with `0x2` (binary: 10)

    Args:
        config: the program's configuration containing board IP and ports
        sock: the UDP socket instance
        address: the address to write to
        data: the data to write
        count: the number of 32-bit words to write
        verify: Optionally verify against a different provided value by ORing it
        write_attempts: The number of times to retry writing and verifying.

    Returns: None

    """
    # read current value
    current_val = read(sock, config.board_ip, address, count, config.read_port)
    # AND mask it with the inverse of new data
    new_value = current_val & ~data
    logger.debug(
        "AND of current value (%s) and inverse of (%s) is %s", current_val, data, new_value
    )
    # write the new value and verify
    write_verify(config, sock, address, new_value, count, verify, write_attempts)


def write_verify(  # noqa: PLR0913 PLR0917
    config: ControlConfig,
    sock: socket.SocketType,
    address: int,
    new_value: int,
    count: int,
    verify: VerifyFunc,
    write_attempts: int = WRITE_ATTEMPTS,
) -> None:
    """Write a value then verify it by reading it back with a retry/timeout loop.

    This function takes an "attempts" argument, which will re-write if the verification times out.

    Args:
        config: the program's configuration containing board IP and ports
        sock: the UDP socket instance
        address: the address to write to
        new_value: the data to write
        count: the number of 32-bit words to write
        verify: Optionally verify against a different provided value by ORing it
        write_attempts: The number of times to retry writing and verifying.

    Returns: None

    """
    current_val = None
    for _ in range(write_attempts):
        write(sock, config.board_ip, address, new_value, count, config.write_port)
        # sleep after writing
        sleep(SLEEP_AFTER_WRITE_S)

        # check to make sure read value is equal to the new (masked) value
        for _ in range(VERIFY_ATTEMPTS):
            current_val = read(sock, config.board_ip, address, count, config.read_port)
            logger.debug("Current value is %s", current_val)
            if verify(current_val):
                return

            sleep(SLEEP_BETWEEN_VERIFY_ATTEMPTS_S)

    raise OSError(
        f"({config.board_ip}) Could not write {count} 32 bit words to address {address} "
        f"(set data={new_value}, readback={current_val})"
    )


def write(  # noqa: PLR0917, PLR0913
    sock: socket.SocketType,
    host: ipaddress.IPv4Address,
    address: int,
    data: int,
    count: int,
    port: int,
) -> None:
    """Write a value.

    This is a low-level function that should just attempt a single write without verifying it.

    Args:
        sock: the UDP socket instance
        host: the streaming control board host IP
        address: the address to write to
        data: the data to write
        count: the number of 32-bit words to write
        port: port to use when writing

    Returns: None

    """
    logger.debug(
        "(%s) writing %s 32-bit words to address %s (data=%s, bin: %s)",
        host,
        count,
        address,
        data,
        bin(data),
    )
    # write request is 32-bit address, 16-bit block size and 32-bit data
    message = (
        address.to_bytes(length=4, byteorder="big")
        + count.to_bytes(length=2, byteorder="big")
        + data.to_bytes(length=4, byteorder="big")
    )
    logger.debug("Writing: %r", message)
    sock.sendto(message, (str(host), port))


def read(
    sock: socket.SocketType, host: ipaddress.IPv4Address, address: int, count: int, port: int
) -> int:
    """Read a register on the streaming control board and return its value.

    This is a 'low-level' function that should just attempt a single read.

    Args:
        sock: the UDP socket instance
        host: the IP address of the streaming control board
        address: the address to read
        count: how many 32-bit words to request when reading.
        port: port to use for reading

    Returns: The received data

    """
    logger.debug("(%s) requesting read %s 32-bit words from address %s", host, count, address)
    sock.settimeout(2.0)

    # request format is 32-bit address + 16 bit block size
    message = address.to_bytes(length=4, byteorder="big") + count.to_bytes(2, byteorder="big")
    logger.debug("Request: %r", message)

    sock.sendto(message, (str(host), port))

    data, recv_host = sock.recvfrom(RECEIVE_BUFFER_SIZE)
    logger.debug("Received: %r", data)

    # for AF_INET recv_host is a tuple of (host, port)
    if str(host) != str(recv_host[0]):
        raise OSError(f"Received data from {recv_host[0]} not from {host}")

    # parse the 32-bit address
    received_address = int.from_bytes(data[:4], byteorder="big")
    if received_address != address:
        raise OSError(
            f"Received address ({received_address}) not same as requested address ({address}))"
        )

    # parse the 16-bit block size
    received_block_size = int.from_bytes(data[4:6], byteorder="big")
    if received_block_size != count:
        raise OSError(
            f"Received block size ({received_block_size}) not same as"
            f" requested block size ({count})"
        )

    # parse the 32-bit data. block size is in 32-bit words,
    # so need to multiply by 4 here as 4*8 bytes is 32 bits.
    data = int.from_bytes(data[6 : 6 + (received_block_size * 4)], byteorder="big")
    logger.debug(
        "Response: addr = %s, block size = %s, data = %s (bin: %s)",
        received_address,
        received_block_size,
        data,
        bin(data),
    )
    return data


def set_board_response_ip(
    config: ControlConfig, sock: socket.SocketType, sock_lock: threading.RLock
) -> None:
    """Set the board's communication register to the local IP address.

    Args:
        config: The program's configuration
        sock: the socket instance to use
        sock_lock: the lock to use when using the socket instance.

    """
    ip = ip_address(config.local_ip)
    ip_int = int.from_bytes(ip.packed, byteorder="big")
    logger.debug("IP IS %s, int repr is %s", ip, ip_int)
    with sock_lock:
        write_verify(
            config,
            sock,
            COMMS_REGISTER.address,
            ip_int,
            COMMS_REGISTER.size,
            verify=lambda x: x == ip_int,
        )
