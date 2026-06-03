from queue import Queue

from kafka_dae_control.pvs.camonitor_callbacks import (
    update_blocks,
    update_title,
    update_users,
)
from kafka_dae_control.worker_event import TitleUpdateEvent, UsersUpdateEvent


def test_update_blocks_with_encoded_blocks_works_correctly():
    encoded = "789c8b56f2730d8f77f2f177f6568a05001a0603b1"
    queue = Queue()
    update_blocks(queue, "blah:", char_value=encoded)

    assert queue.get_nowait().value == ["blah:CS:SB:NEW_BLOCK"]


def test_update_title_adds_title_update_to_queue():
    q = Queue()
    update_title(q, char_value="blah")
    val = q.get_nowait()
    assert isinstance(val, TitleUpdateEvent)
    assert val.value == "blah"


def test_update_users_adds_users_update_to_queue():
    q = Queue()
    update_users(q, char_value="user1")
    val = q.get_nowait()
    assert isinstance(val, UsersUpdateEvent)
    assert val.value == "user1"
