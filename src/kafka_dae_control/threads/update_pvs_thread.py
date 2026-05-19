"""Thread for updating PV values by calling posts on each PV on an interval."""

import logging
from time import sleep
from typing import Never

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.data import Data
from kafka_dae_control.pvs.static_pvs import StaticPVs

logger = logging.getLogger(__name__)


def update_pvs_thread(static_pvs: StaticPVs, data: Data, config: ControlConfig) -> Never:
    """Thread for updating PV values by calling posts on each PV on an interval.

    Args:
        static_pvs: the p4p static PVs object
        data: the data class to read PV data from
        config: the program's configuration

    """
    while True:
        try:
            static_pvs.update_all(data)
        except Exception:
            logger.exception("PV update failed: ")
        sleep(config.pv_update_interval_s)
