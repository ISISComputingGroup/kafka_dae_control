import ipaddress
import re
from unittest.mock import Mock, call, patch

import pytest

from kafka_dae_control.comms import (
    ATTEMPTS,
    SLEEP_AFTER_WRITE_S,
    SLEEP_BETWEEN_ATTEMPTS_S,
    read,
    write,
    write_and_inv_then_verify,
    write_verify,
)
from kafka_dae_control.defaults import (
    COMMS_REGISTER,
    READ_PORT,
    RECEIVE_BUFFER_SIZE,
    RUNNING_REGISTER,
    WRITE_PORT,
)
from kafka_dae_control.run_state import RunRegister

HOST = ipaddress.IPv4Address("192.168.1.100")


def _read_response(address: int, block_size: int, data: int) -> bytes:
    return (
        address.to_bytes(4, "big")
        + block_size.to_bytes(2, "big")
        + data.to_bytes(block_size * 4, "big")
    )


def test_write_sets_register():
    sock = Mock()
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    write(sock, HOST, RUNNING_REGISTER.address, data, RUNNING_REGISTER.size)

    sock.sendto.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x13",
        (str(HOST), WRITE_PORT),
    )


def test_read_returns_result():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(
            RUNNING_REGISTER.address,
            RUNNING_REGISTER.size,
            RunRegister.STATUS_RUNNING,
        ),
        (HOST, READ_PORT),
    )

    result = read(sock, HOST, RUNNING_REGISTER.address, RUNNING_REGISTER.size)

    assert result == RunRegister.STATUS_RUNNING
    sock.settimeout.assert_called_once_with(2.0)
    sock.sendto.assert_called_once_with(b"\x00\x00\x00\x00\x00\x01", (str(HOST), READ_PORT))
    sock.recvfrom.assert_called_once_with(RECEIVE_BUFFER_SIZE)


def test_read_raises_when_response_address_does_not_match_request():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(COMMS_REGISTER.address, COMMS_REGISTER.size, 0),
        (HOST, READ_PORT),
    )

    with pytest.raises(
        OSError, match=re.escape("Received address (268435492) not same as requested address (0)")
    ):
        read(sock, HOST, RUNNING_REGISTER.address, RUNNING_REGISTER.size)


def test_read_raises_when_response_host_does_not_match_request():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(RUNNING_REGISTER.address, RUNNING_REGISTER.size, 0),
        ("192.168.1.101", READ_PORT),
    )
    with pytest.raises(
        OSError, match=re.escape("Received data from 192.168.1.101 not from 192.168.1.100")
    ):
        read(sock, HOST, RUNNING_REGISTER.address, RUNNING_REGISTER.size)


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", side_effect=[0, RunRegister.STATUS_RUNNING])
@patch("kafka_dae_control.comms.write")
def test_write_verify_sets_and_retries(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType
):
    sock = Mock()
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    write_verify(
        sock,
        HOST,
        RUNNING_REGISTER.address,
        data,
        RUNNING_REGISTER.size,
        verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
    )

    mock_write.assert_called_once_with(
        sock,
        HOST,
        RUNNING_REGISTER.address,
        data,
        RUNNING_REGISTER.size,
    )
    assert mock_read.call_args_list == [
        call(sock, HOST, RUNNING_REGISTER.address, RUNNING_REGISTER.size),
        call(sock, HOST, RUNNING_REGISTER.address, RUNNING_REGISTER.size),
    ]
    mock_sleep.assert_has_calls([call(SLEEP_AFTER_WRITE_S), call(SLEEP_BETWEEN_ATTEMPTS_S)])


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", return_value=0)
@patch("kafka_dae_control.comms.write")
def test_write_verify_raises_after_retry_limit(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType
):
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    with pytest.raises(OSError, match="Could not write"):
        write_verify(
            Mock(),
            HOST,
            RUNNING_REGISTER.address,
            data,
            RUNNING_REGISTER.size,
            verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
        )

    mock_write.assert_called_once()
    assert mock_read.call_count == ATTEMPTS
    mock_sleep.assert_has_calls(
        [call(SLEEP_AFTER_WRITE_S)] + [call(SLEEP_BETWEEN_ATTEMPTS_S)] * ATTEMPTS
    )


@patch("kafka_dae_control.comms.write_verify")
@patch(
    "kafka_dae_control.comms.read",
    return_value=RunRegister.ETHERNET_OVERRIDE | RunRegister.STATUS_RUNNING,
)
def test_write_and_inv_then_verify_clears_bit(
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_write_verify,  # pyright: ignore reportMissingParameterType
):
    sock = Mock()
    verify = Mock()

    write_and_inv_then_verify(
        sock,
        HOST,
        RUNNING_REGISTER.address,
        RunRegister.ETHERNET_OVERRIDE,
        RUNNING_REGISTER.size,
        verify,
    )

    mock_read.assert_called_once_with(
        sock,
        HOST,
        RUNNING_REGISTER.address,
        RUNNING_REGISTER.size,
    )
    mock_write_verify.assert_called_once_with(
        sock,
        HOST,
        RUNNING_REGISTER.address,
        RunRegister.STATUS_RUNNING,
        RUNNING_REGISTER.size,
        verify,
    )
