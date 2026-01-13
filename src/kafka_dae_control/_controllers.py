"""ISIS Kafka DAE Control."""
from enum import IntEnum
from logging import getLogger

from fastcs.attributes import AttrR
from fastcs.controllers import Controller
from fastcs.methods import command
from fastcs.datatypes.enum import Enum

from kafka_dae_control._io import VxiUdpIORef, VxiUdpIO
from kafka_dae_control._types import Runstate

logger = getLogger(__name__)

class KafkaDaeController(Controller):
    """FastCS Controller for a VXI Streaming board."""

    def __init__(self) -> None:
        connection = None

        super().__init__(ios=[VxiUdpIO(connection=connection)])

    async def connect(self) -> None:
        pass


    async def initialise(self) -> None:
        self.runstate = AttrR(Enum(Runstate), io_ref=VxiUdpIORef(update_period=1.0, register_address=0x00), initial_value=Runstate.PROCESSING)

    @command()
    async def begin(self):
        logger.info("Executed begin")

    @command()
    async def end(self):
        logger.info("Executed end")
