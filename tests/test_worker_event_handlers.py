import ipaddress
from queue import Queue
from threading import RLock
from unittest.mock import MagicMock, Mock, patch

import pytest
from confluent_kafka import KafkaError, Message
from streaming_data_types import deserialise_6s4t, deserialise_pl72

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import FRAME_SYNC_SEL_REGISTER, FrameSyncSelect, RunRegister
from kafka_dae_control.event_with_value import EventWithValue
from kafka_dae_control.worker_event_handlers import (
    delivery_report_run_info,
    handle_begin,
    handle_end,
    handle_frame_sync_sp_change,
)


def test_beginning_starts_hardware_sends_run_start_and_sets_running(
    data: Data, conf: ControlConfig
):
    conf.instrument_name = "TESTINST"
    data.run_number = 123
    data.running = False
    producer = Mock()
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    done_event = Mock()

    conf.board_ip = ipaddress.IPv4Address("127.0.0.1")
    conf.runinfo_topic = "run-info-topic"

    nexus_structure = '{"this_is_some_valid": "json"}'

    with (
        patch("kafka_dae_control.worker_event_handlers.write_verify") as write_verify,
        patch(
            "kafka_dae_control.worker_event_handlers.generate_nexus_structure",
            return_value=nexus_structure,
        ),
    ):
        producer.flush.side_effect = done_event.set()

        handle_begin(
            data=data,
            config=conf,
            producer=producer,
            sock=sock,
            sock_lock=sock_lock,
            done_event=done_event,
            queue=Queue(),
        )

        write_verify.assert_called_once()
        (
            _,
            _,
            _,
            register_value,
            _,
        ) = write_verify.call_args.args
        assert register_value == (
            RunRegister.ETHERNET_OVERRIDE
            | RunRegister.RUN_SIGNAL_ETH
            | RunRegister.STREAM_EMPTY_FRAMES
        )

        producer.produce.assert_called_once()
        topic, blob = producer.produce.call_args.args
        assert topic == "run-info-topic"

        run_start = deserialise_pl72(blob)
        assert run_start.job_id == data.job_id
        assert run_start.instrument_name == "TESTINST"
        assert run_start.control_topic == "run-info-topic"
        assert run_start.run_name == "TESTINST123"
        assert run_start.nexus_structure == nexus_structure

        producer.flush.assert_called_once()
        assert sock_lock.__enter__.called
        assert done_event.set.called


def test_ending_stops_hardware_sends_run_stop_sets_setup_and_increments_run_number(
    data: Data, conf: ControlConfig
):
    data.job_id = "job-id-123"
    data.run_number = 7
    data.running = True
    producer = Mock()
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    done_event = Mock()

    conf.board_ip = ipaddress.IPv4Address("127.0.0.1")
    conf.runinfo_topic = "run-info-topic"

    with patch(
        "kafka_dae_control.worker_event_handlers.write_and_inv_then_verify"
    ) as write_and_inv_then_verify:
        producer.flush.side_effect = done_event.set()
        handle_end(
            data=data,
            config=conf,
            producer=producer,
            sock=sock,
            sock_lock=sock_lock,
            done_event=done_event,
            queue=Queue(),
        )

        write_and_inv_then_verify.assert_called_once()
        (
            _,
            _,
            _,
            register_value,
            _,
        ) = write_and_inv_then_verify.call_args.args
        assert register_value == RunRegister.ETHERNET_OVERRIDE

        producer.produce.assert_called_once()
        topic, blob = producer.produce.call_args.args
        assert topic == "run-info-topic"

        run_stop = deserialise_6s4t(blob)
        assert run_stop.job_id == "job-id-123"

        producer.flush.assert_called_once()
        assert data.run_number == 8

        assert sock_lock.__enter__.called
        assert done_event.set.called


def test_exception_during_begin_logs(
    data: Data, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    data.running = False
    sock_lock = MagicMock(spec=RLock())
    sock_lock.__enter__.side_effect = Exception
    handle_begin(
        conf,
        data,
        Mock(),
        Mock(),
        sock_lock,
        Mock(),
        Queue(),
    )
    assert "Failed to start run:" in caplog.text


def test_exception_during_end_logs(
    data: Data, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    data.running = True
    sock_lock = MagicMock(spec=RLock())
    sock_lock.__enter__.side_effect = Exception
    handle_end(
        conf,
        data,
        Mock(),
        Mock(),
        sock_lock,
        Mock(),
        Queue(),
    )
    assert "Failed to end run:" in caplog.text


def test_exception_during_begin_if_already_running(
    data: Data, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    data.running = True
    sock_lock = MagicMock(spec=RLock())
    handle_begin(conf, data, Mock(), Mock(), sock_lock, Mock(), Queue())
    assert "The hardware is already running - doing nothing" in caplog.text


def test_exception_during_end_if_not_running(
    data: Data, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    data.running = False
    sock_lock = MagicMock(spec=RLock())
    handle_end(
        conf,
        data,
        Mock(),
        Mock(),
        sock_lock,
        Mock(),
        Queue(),
    )
    assert "The hardware is already not running - doing nothing" in caplog.text


def test_delivery_report_cb_sets_error_if_error():
    done_event = EventWithValue()
    error = KafkaError(error=KafkaError.KAFKA_STORAGE_ERROR)  # pyright: ignore[reportCallIssue]
    delivery_report_run_info(done_event, error, Message())
    assert "Error with kafka delivery: KAFKA_STORAGE_ERROR" in str(done_event.err)
    assert done_event._ev.is_set()


def test_delivery_report_cb_calls_set_if_no_error():
    done_event = EventWithValue()
    msg = Message(topic="mytopic123", value=b"myvalue234")
    delivery_report_run_info(done_event, None, msg)
    assert done_event._ev.is_set()


@pytest.mark.parametrize(
    "frame_sync_select",
    [FrameSyncSelect.INTERNAL_TEST_CLOCK, FrameSyncSelect.SMP, FrameSyncSelect.ISIS],
)
@patch("kafka_dae_control.worker_event_handlers.write_verify")
def test_frame_sync_select_change_writes_to_hardware(
    mock_write_verify: Mock, data: Data, conf: ControlConfig, frame_sync_select: FrameSyncSelect
):
    done_event = EventWithValue()
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    handle_frame_sync_sp_change(frame_sync_select, conf, data, sock, sock_lock, done_event)
    assert mock_write_verify.call_args[0][2] == FRAME_SYNC_SEL_REGISTER.address
    assert mock_write_verify.call_args[0][3] == frame_sync_select.value
    assert mock_write_verify.call_args[0][4] == FRAME_SYNC_SEL_REGISTER.size
    assert done_event._ev.is_set()


@patch("kafka_dae_control.worker_event_handlers.write_verify", side_effect=Exception)
def test_frame_sync_select_failed_to_write_sets_err(
    m: Mock,
    data: Data,
    conf: ControlConfig,
):
    done_event = EventWithValue()
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    handle_frame_sync_sp_change(
        FrameSyncSelect.INTERNAL_TEST_CLOCK, conf, data, sock, sock_lock, done_event
    )
    assert done_event.err is not None
    assert done_event._ev.is_set()
