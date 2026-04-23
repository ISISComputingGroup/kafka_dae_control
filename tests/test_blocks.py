from kafka_dae_control.blocks import update_blocks
from kafka_dae_control.data import Data


def test_update_blocks_with_encoded_blocks_works_correctly():
    encoded = '789c8b56f2730d8f77f2f177f6568a05001a0603b1'
    data = Data()
    update_blocks("blah", data, char_value=encoded)
    assert data.blocks == ["blahCS:SB:NEW_BLOCK"]
