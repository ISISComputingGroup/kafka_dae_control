from queue import Queue

from kafka_dae_control.pvs.blocks import update_blocks


def test_update_blocks_with_encoded_blocks_works_correctly():
    encoded = "789c8b56f2730d8f77f2f177f6568a05001a0603b1"
    queue = Queue()
    update_blocks(queue, "blah:", char_value=encoded)

    assert queue.get_nowait().value == ["blah:CS:SB:NEW_BLOCK"]
