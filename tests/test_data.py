from kafka_dae_control.data import Data


def test_all_vetoes():
    d = Data()
    d.soft_vetoes_array = [0, 1, 0, 1]
    d.hard_vetoes_array = [1, 0, 1, 0]

    assert d.all_vetoes == 0b1111
