import argparse
import asyncio
import logging
import socket

from fastcs.launch import FastCS
from fastcs.logging import LogLevel, configure_logging

from kafka_dae_control._controllers import KafkaDaeController
from fastcs.transports import EpicsIOCOptions, EpicsPVATransport, EpicsCATransport


if __name__ == "__main__":



    parser = argparse.ArgumentParser(description="Demo PVA ioc")
    parser.add_argument("-i", "--ip", type=str, default="127.0.0.1", help="IP to connect to")
    parser.add_argument("-p", "--port", type=int, help="Port to connect to")
    args = parser.parse_args()

    configure_logging(level=LogLevel.DEBUG)
    logging.basicConfig(level=LogLevel.DEBUG)

    asyncio.get_event_loop().slow_callback_duration = 1000

    epics_options = EpicsIOCOptions(pv_prefix=f"TE:{socket.gethostname().upper()}:KDAECTRL")
    epics_ca = EpicsCATransport(epicsca=epics_options)
    epics_pva = EpicsPVATransport(epicspva=epics_options)

    controller = KafkaDaeController()

    fastcs = FastCS(
        controller,
        [epics_ca, epics_pva],
    )
    fastcs.run(interactive=True)
