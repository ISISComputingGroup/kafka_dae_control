from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from typing import TypeAlias

from fastcs.attributes import AttributeIORef, AttributeIO, AttrR, AttrW

from kafka_dae_control._types import Runstate

logger = getLogger(__name__)
T: TypeAlias = int | float | Enum | bool

@dataclass
class VxiUdpIORef(AttributeIORef):
    register_address: int = 0


class VxiUdpIO(AttributeIO[T, VxiUdpIORef]):

    def __init__(self, connection) -> None:
        super().__init__()
        self._connection = connection

    async def update(self, attr: AttrR[T, VxiUdpIORef]) -> None:
        try:
            logger.info("SETTING RUNSTATE TO SETUP")
            await attr.update(Runstate.SETUP)
        except Exception as e:
            pass


    async def send(self, attr: AttrW[T, VxiUdpIORef], value: T) -> None:
        try:
            logger.info("WRITING TO DEVICE")
            pass
        except Exception as e:
            pass
