import ipaddress
import re
from threading import RLock
from unittest.mock import MagicMock, Mock, call, patch

import pytest

from kafka_dae_control.comms import (
    SLEEP_AFTER_WRITE_S,
    SLEEP_BETWEEN_VERIFY_ATTEMPTS_S,
    VERIFY_ATTEMPTS,
    read,
    set_board_response_ip,
    write,
    write_and_inv_then_verify,
    write_verify,
)
from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import (
    READ_PORT,
    RECEIVE_BUFFER_SIZE,
    WRITE_PORT,
    RunRegister,
)

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

    write(sock, HOST, 0, data, 1, WRITE_PORT)

    sock.sendto.assert_called_once_with(
        b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x13",
        (str(HOST), WRITE_PORT),
    )


def test_read_returns_result():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(
            0,
            1,
            RunRegister.STATUS_RUNNING,
        ),
        (HOST, READ_PORT),
    )

    result = read(sock, HOST, 0, 1, READ_PORT)

    assert result == RunRegister.STATUS_RUNNING
    sock.settimeout.assert_called_once_with(2.0)
    sock.sendto.assert_called_once_with(b"\x00\x00\x00\x00\x00\x01", (str(HOST), READ_PORT))
    sock.recvfrom.assert_called_once_with(RECEIVE_BUFFER_SIZE)


def test_read_raises_when_response_address_does_not_match_request():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(268435492, 1, 0),
        (HOST, READ_PORT),
    )

    with pytest.raises(
        OSError, match=re.escape("Received address (268435492) not same as requested address (0)")
    ):
        read(sock, HOST, 0, 1, READ_PORT)


def test_read_raises_when_returned_block_size_not_same_as_requested():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(268435492, 1 + 1, 0),
        (HOST, READ_PORT),
    )

    with pytest.raises(
        OSError, match=re.escape("Received block size (2) not same as requested block size (1)")
    ):
        read(sock, HOST, 268435492, 1, READ_PORT)


def test_read_raises_when_response_host_does_not_match_request():
    sock = Mock()
    sock.recvfrom.return_value = (
        _read_response(0, 1, 0),
        ("192.168.1.101", READ_PORT),
    )
    with pytest.raises(
        OSError, match=re.escape("Received data from 192.168.1.101 not from 192.168.1.100")
    ):
        read(sock, HOST, 0, 1, READ_PORT)


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", side_effect=[0, RunRegister.STATUS_RUNNING])
@patch("kafka_dae_control.comms.write")
def test_write_verify_sets_and_retries(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType,
    conf: ControlConfig,
):
    conf.board_ip = HOST
    sock = Mock()
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    write_verify(
        conf,
        sock,
        0,
        data,
        verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
        count=1,
        write_attempts=1,
    )

    mock_write.assert_called_once_with(sock, HOST, 0, data, 1, WRITE_PORT)
    assert mock_read.call_args_list == [
        call(sock, HOST, 0, 1, READ_PORT),
        call(sock, HOST, 0, 1, READ_PORT),
    ]
    mock_sleep.assert_has_calls([call(SLEEP_AFTER_WRITE_S), call(SLEEP_BETWEEN_VERIFY_ATTEMPTS_S)])


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", return_value=0)
@patch("kafka_dae_control.comms.write")
def test_write_verify_raises_after_retry_limit(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    with pytest.raises(OSError, match="Could not write"):
        write_verify(
            conf,
            Mock(),
            0,
            data,
            verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
            count=1,
            write_attempts=1,
        )

    mock_write.assert_called_once()
    assert mock_read.call_count == VERIFY_ATTEMPTS
    mock_sleep.assert_has_calls(
        [call(SLEEP_AFTER_WRITE_S)] + [call(SLEEP_BETWEEN_VERIFY_ATTEMPTS_S)] * VERIFY_ATTEMPTS
    )


@patch("kafka_dae_control.comms.write_verify")
@patch(
    "kafka_dae_control.comms.read",
    return_value=RunRegister.ETHERNET_OVERRIDE | RunRegister.STATUS_RUNNING,
)
def test_write_and_inv_then_verify_clears_bit(
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_write_verify,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):
    conf.board_ip = HOST
    sock = Mock()
    verify = Mock()

    write_and_inv_then_verify(
        conf,
        sock,
        0,
        RunRegister.ETHERNET_OVERRIDE,
        verify,
        1,
        3,
    )

    mock_read.assert_called_once_with(sock, HOST, 0, 1, READ_PORT)
    mock_write_verify.assert_called_once_with(
        conf,
        sock,
        0,
        RunRegister.STATUS_RUNNING,
        verify,
        1,
        3,
    )


@patch("kafka_dae_control.comms.write_verify")
def test_set_board_response_ip_sets_ip(mock_write_verify, conf: ControlConfig):  # pyright: ignore reportMissingParameterType
    conf.board_ip = ipaddress.IPv4Address("192.168.1.100")
    conf.local_ip = ipaddress.IPv4Address("192.168.1.101")
    lock = MagicMock(spec=RLock())

    sock = Mock()

    set_board_response_ip(conf, sock, lock)

    assert lock.__enter__.called
    assert mock_write_verify.call_args[0][3] == 3232235877


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", return_value=0)
@patch("kafka_dae_control.comms.write")
def test_write_verify_retries(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):
    data = (
        RunRegister.ETHERNET_OVERRIDE | RunRegister.RUN_SIGNAL_ETH | RunRegister.STREAM_EMPTY_FRAMES
    )

    with pytest.raises(OSError, match="Could not write"):
        write_verify(
            conf,
            Mock(),
            0,
            data,
            verify=lambda x: x & RunRegister.STATUS_RUNNING != 0,
            count=1,
            write_attempts=2,
        )

    assert mock_write.call_count == 2


@patch("kafka_dae_control.comms.sleep")
@patch("kafka_dae_control.comms.read", return_value=11)
@patch("kafka_dae_control.comms.write")
def test_inv_write_verify_retries(
    mock_write,  # pyright: ignore reportMissingParameterType
    mock_read,  # pyright: ignore reportMissingParameterType
    mock_sleep,  # pyright: ignore reportMissingParameterType
    conf: ControlConfig,
):

    with pytest.raises(OSError, match="Could not write"):
        write_and_inv_then_verify(
            conf,
            Mock(),
            0,
            RunRegister.ETHERNET_OVERRIDE,
            verify=lambda x: x == "this will never be the same as the register value",  # pyright: ignore reportUnnecessaryComparison
            count=1,
            write_attempts=2,
        )

    assert mock_write.call_count == 2
