from unittest.mock import Mock, patch

import pytest

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.pvs.static_pvs import StaticPVs
from kafka_dae_control.threads.update_pvs_thread import update_pvs_thread


@patch("kafka_dae_control.threads.update_pvs_thread.sleep", side_effect=Exception)
def test_update_pvs_thread(mock_sleep: Mock, data: Data, conf: ControlConfig):

    data.run_number = 12345
    data.running = True

    pvs = Mock(Spec=StaticPVs)
    with pytest.raises(Exception):  # noqa: B017, PT011
        update_pvs_thread(pvs, data, conf)
    pvs.update_all.assert_called_once_with(data)


@patch("kafka_dae_control.threads.update_pvs_thread.sleep", side_effect=Exception)
def test_update_pvs_thread_catches_exception_and_logs_it(
    mock_sleep: Mock, data: Data, conf: ControlConfig, caplog: pytest.LogCaptureFixture
):
    pvs = Mock(spec=StaticPVs)
    pvs.update_all.side_effect = Exception
    with pytest.raises(Exception):  # noqa: B017, PT011
        update_pvs_thread(pvs, data, conf)
    assert "PV update failed:" in caplog.text
