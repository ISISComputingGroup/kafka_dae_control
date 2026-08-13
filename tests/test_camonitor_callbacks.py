from queue import PriorityQueue

from kafka_dae_control.pvs.camonitor_callbacks import (
    run_control_update_callback,
    update_blocks,
)


def test_update_blocks_with_encoded_blocks_works_correctly():
    encoded = "789c8b56f2730d8f77f2f177f6568a05001a0603b1"
    queue = PriorityQueue()
    update_blocks(queue, "blah:", char_value=encoded)

    assert queue.get_nowait().item.value == ["blah:CS:SB:NEW_BLOCK"]


def test_run_control_update_puts_update_on_queue():
    q = PriorityQueue()
    run_control_update_callback(q, value=1)
    run_control_update_callback(q, value=0)

    assert not q.get_nowait().item.value
    assert q.get_nowait().item.value
