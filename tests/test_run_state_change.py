from unittest.mock import Mock, patch

from streaming_data_types import deserialise_6s4t, deserialise_pl72

from kafka_dae_control.data import Data
from kafka_dae_control.run_state import RunRegister, RunState, on_run_state_change


def test_beginning_starts_hardware_sends_run_start_and_sets_running():
    data = Data()
    data.instrument_name = "TESTINST"
    data.run_number.value = 123
    producer = Mock()
    sock = Mock()

    nexus_structure = '{"this_is_some_valid": "json"}'

    with (
        patch("kafka_dae_control.run_state.write_verify") as write_verify,
        patch("kafka_dae_control.run_state.generate_nexus_structure", return_value=nexus_structure),
    ):
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=sock,
            host="127.0.0.1",
            old_value=RunState.SETUP,  # pyright: ignore[reportArgumentType]
            new_value=RunState.BEGINNING,  # pyright: ignore[reportArgumentType]
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
        assert run_start.job_id == data.job_id.value
        assert run_start.instrument_name == "TESTINST"
        assert run_start.control_topic == "run-info-topic"
        assert run_start.run_name == "123"
        assert run_start.nexus_structure == nexus_structure

        producer.flush.assert_called_once()
        assert data.run_state.value == RunState.RUNNING  # pyright: ignore[reportArgumentType]


def test_beginning_restores_old_state_when_hardware_write_fails():
    data = Data()
    data.run_state.value = RunState.BEGINNING
    producer = Mock()

    with patch(
        "kafka_dae_control.run_state.write_verify",
        side_effect=OSError("sending to hardware failed"),
    ):
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.SETUP,  # pyright: ignore[reportArgumentType]
            new_value=RunState.BEGINNING,  # pyright: ignore[reportArgumentType]
        )

        assert data.run_state.value == RunState.SETUP  # pyright: ignore[reportArgumentType]
        producer.produce.assert_not_called()
        producer.flush.assert_not_called()


def test_ending_stops_hardware_sends_run_stop_sets_setup_and_increments_run_number():
    data = Data()
    data.job_id.value = "job-id-123"
    data.run_number.value = 7
    producer = Mock()

    with patch(
        "kafka_dae_control.run_state.write_and_inv_then_verify"
    ) as write_and_inv_then_verify:
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.RUNNING,  # pyright: ignore[reportArgumentType]
            new_value=RunState.ENDING,  # pyright: ignore[reportArgumentType]
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
        assert data.run_state.value == RunState.SETUP  # pyright: ignore[reportArgumentType]
        assert data.run_number.value == 8


def test_ending_restores_old_state_when_hardware_write_fails():
    data = Data()
    data.run_state.value = RunState.ENDING
    data.run_number.value = 7
    producer = Mock()

    with patch(
        "kafka_dae_control.run_state.write_and_inv_then_verify",
        side_effect=OSError("sending to hardware failed"),
    ):
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.RUNNING,  # pyright: ignore[reportArgumentType]
            new_value=RunState.ENDING,  # pyright: ignore[reportArgumentType]
        )

        assert data.run_state.value == RunState.RUNNING  # pyright: ignore[reportArgumentType]
        assert data.run_number.value == 7
        producer.produce.assert_not_called()
        producer.flush.assert_not_called()


def test_pausing_stops_hardware_without_sending_kafka_message():
    data = Data()
    producer = Mock()

    with patch(
        "kafka_dae_control.run_state.write_and_inv_then_verify"
    ) as write_and_inv_then_verify:
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.RUNNING,  # pyright: ignore[reportArgumentType]
            new_value=RunState.PAUSING,  # pyright: ignore[reportArgumentType]
        )

        write_and_inv_then_verify.assert_called_once()
        assert data.run_state.value == RunState.PAUSED  # pyright: ignore[reportArgumentType]
        producer.produce.assert_not_called()
        producer.flush.assert_not_called()


def test_resuming_starts_hardware_without_sending_kafka_message():
    data = Data()
    producer = Mock()

    with patch("kafka_dae_control.run_state.write_verify") as write_verify:
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.PAUSED,  # pyright: ignore[reportArgumentType]
            new_value=RunState.RESUMING,  # pyright: ignore[reportArgumentType]
        )

        write_verify.assert_called_once()
        assert data.run_state.value == RunState.RUNNING  # pyright: ignore[reportArgumentType]
        producer.produce.assert_not_called()
        producer.flush.assert_not_called()


def test_other_run_state_does_not_write_or_send_kafka_message():
    data = Data()
    data.run_state.value = RunState.SETUP
    producer = Mock()

    with (
        patch("kafka_dae_control.run_state.write_verify") as write_verify,
        patch("kafka_dae_control.run_state.write_and_inv_then_verify") as write_and_inv_then_verify,
    ):
        on_run_state_change(
            data=data,
            producer=producer,
            run_info_topic="run-info-topic",
            sock=Mock(),
            host="127.0.0.1",
            old_value=RunState.SETUP,  # pyright: ignore[reportArgumentType]
            new_value=RunState.RUNNING,  # pyright: ignore[reportArgumentType]
        )

        write_verify.assert_not_called()
        write_and_inv_then_verify.assert_not_called()
        producer.produce.assert_not_called()


def test_pausing_when_hardware_error_occurs_raises_and_leaves_runstate():
    producer = Mock()
    d = Data(run_state=RunState.RUNNING)

    with patch(
        "kafka_dae_control.run_state.write_and_inv_then_verify",
        side_effect=OSError("hardware error"),
    ):
        on_run_state_change(
            data=d,
            producer=producer,
            sock=Mock(),
            run_info_topic="run-info-topic",
            host="127.0.0.1",
            old_value=RunState.RUNNING,  # pyright: ignore[reportArgumentType]
            new_value=RunState.PAUSING,  # pyright: ignore[reportArgumentType]
        )

    assert d.run_state.value == RunState.RUNNING  # pyright: ignore[reportArgumentType]
    producer.produce.assert_not_called()


def test_resuming_when_hardware_error_occurs_raises_and_leaves_runstate():
    producer = Mock()
    d = Data(run_state=RunState.PAUSED)

    with patch("kafka_dae_control.run_state.write_verify", side_effect=OSError("hardware error")):
        on_run_state_change(
            data=d,
            producer=producer,
            sock=Mock(),
            run_info_topic="run-info-topic",
            host="127.0.0.1",
            old_value=RunState.PAUSED,  # pyright: ignore[reportArgumentType]
            new_value=RunState.RESUMING,  # pyright: ignore[reportArgumentType]
        )

    assert d.run_state.value == RunState.PAUSED  # pyright: ignore[reportArgumentType]
    producer.produce.assert_not_called()
