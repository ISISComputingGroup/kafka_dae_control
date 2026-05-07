import ipaddress
from functools import partial
from unittest.mock import Mock, patch

from kafka_dae_control.data import Data
from kafka_dae_control.hooks import setup_hooks
from kafka_dae_control.run_state import on_run_state_change


def test_setup_hooks_sets_up_hooks():
    d = Data()
    with patch("kafka_dae_control.hooks.save_file") as save_file:
        setup_hooks(
            d,
            Mock(),
            "",
            Mock(),
            ipaddress.IPv4Address("127.0.0.1"),
        )

    assert on_run_state_change == d.run_state.callbacks[0].func

    assert partial(save_file, d).func == d.title.callbacks[0].func
    assert partial(save_file, d).func == d.users.callbacks[0].func
    assert partial(save_file, d).func == d.job_id.callbacks[0].func
    assert partial(save_file, d).func == d.run_number.callbacks[0].func

    assert partial(save_file, d).args == d.title.callbacks[0].args
    assert partial(save_file, d).args == d.users.callbacks[0].args
    assert partial(save_file, d).args == d.job_id.callbacks[0].args
    assert partial(save_file, d).args == d.run_number.callbacks[0].args
