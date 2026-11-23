import pytest

from kafka_dae_control.data import DetectorSpectraMapping


def test_detspecmap_validator():
    with pytest.raises(ValueError, match=r".*Detector ID must be unique. Offending ID: 1.*"):
        DetectorSpectraMapping.model_validate([{"det": 1, "spec": 1}, {"det": 1, "spec": 2}])
