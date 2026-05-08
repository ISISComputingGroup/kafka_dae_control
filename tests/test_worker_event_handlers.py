import ipaddress
from threading import RLock
from unittest.mock import MagicMock, Mock, patch

from _pytest.logging import LogCaptureFixture
from streaming_data_types import deserialise_6s4t, deserialise_pl72

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.defaults import RunRegister
from kafka_dae_control.worker_event_handlers import handle_begin, handle_end


def test_beginning_starts_hardware_sends_run_start_and_sets_running(
    data: Data, conf: ControlConfig
):
    data.instrument_name = "TESTINST"
    data.run_number = 123
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
        handle_begin(
            data=data,
            config=conf,
            producer=producer,
            sock=sock,
            sock_lock=sock_lock,
            done_event=done_event,
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
        assert run_start.run_name == "123"
        assert run_start.nexus_structure == nexus_structure

        producer.flush.assert_called_once()
        assert sock_lock.__enter__.called
        assert done_event.set.called


def test_ending_stops_hardware_sends_run_stop_sets_setup_and_increments_run_number(
    data: Data, conf: ControlConfig
):
    data.job_id = "job-id-123"
    data.run_number = 7
    producer = Mock()
    sock = Mock()
    sock_lock = MagicMock(spec=RLock())
    done_event = Mock()

    conf.board_ip = ipaddress.IPv4Address("127.0.0.1")
    conf.runinfo_topic = "run-info-topic"

    with patch(
        "kafka_dae_control.worker_event_handlers.write_and_inv_then_verify"
    ) as write_and_inv_then_verify:
        handle_end(
            data=data,
            config=conf,
            producer=producer,
            sock=sock,
            sock_lock=sock_lock,
            done_event=done_event,
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


def test_exception_during_begin_logs(data: Data, conf: ControlConfig, caplog: LogCaptureFixture):
    sock_lock = MagicMock(spec=RLock())
    sock_lock.__enter__.side_effect = Exception
    handle_begin(conf, data, Mock(), Mock(), sock_lock, Mock())
    assert "Failed to start run:" in caplog.text


def test_exception_during_end_logs(data: Data, conf: ControlConfig, caplog: LogCaptureFixture):
    sock_lock = MagicMock(spec=RLock())
    sock_lock.__enter__.side_effect = Exception
    handle_end(conf, data, Mock(), Mock(), sock_lock, Mock())
    assert "Failed to end run:" in caplog.text
