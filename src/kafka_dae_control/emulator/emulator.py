"""An SCB emulator for simulation mode."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from lewis.adapters.stream import Cmd
from lewis.adapters.udp import UDPInterface
from lewis.core.logging import has_log
from lewis.core.simulation import Simulation
from lewis.devices import Device

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import Registers, RunRegister

logger = logging.getLogger(__name__)


def _be_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big")


def _be_words(b: bytes) -> list[int]:
    return [int.from_bytes(b[i : i + 4], byteorder="big") for i in range(0, len(b), 4)]


@dataclass
class Register:
    """Represents an individual register on the streaming control board."""

    name: str
    """The register `id` from the firmware xml"""
    value: int
    """The current register value"""
    side_effect: Callable[[int], int] | None = None
    """A side effect to call on the current value when set.
     input argument is the new value, output is the new value with
      whatever side effect has been applied to it"""


class SCBDevice(Device):
    """Device class for the streaming control board."""

    registers: dict[int, Register] = {}  # ruff: ignore [mutable-class-default]
    """mapping of address - name/value"""


@has_log
class SCBInterface(UDPInterface):
    """Stream interface for the streaming control board."""

    commands = {  # ruff: ignore [mutable-class-default]
        Cmd(
            "read",
            pattern=r"(?s)\A(.{4})(.{2})\Z",
            return_mapping=None,
            argument_mappings=(_be_int, _be_int),
        ),
        Cmd(
            "write",
            pattern=r"(?s)\A(.{4})(.{2})(.{4})\Z",
            return_mapping=None,
            argument_mappings=(_be_int, _be_int, _be_words),
        ),
    }

    def read(self, addr: int, block_size: int) -> bytes | None:
        """Read a register value.

        Args:
            addr: register address.
            block_size: block size to read.

        Returns: the data in the requested register.

        """
        self.log.debug("read received - addr:%s block size:%s", addr, block_size)
        # read - return the address, block size and read data
        if addr in self.device.registers:
            val = self.device.registers[addr].value
            self.log.debug("read %s from %s", val, addr)
            to_return = (
                addr.to_bytes(4, byteorder="big")
                + block_size.to_bytes(2, byteorder="big")
                + val.to_bytes(block_size * 4, byteorder="big")
            )
            self.log.debug("Returning %s", to_return)
            return to_return
        else:
            self.log.error("invalid read address %s", addr)
            return None

    def write(self, addr: int, block_size: int, data: list[int]) -> None:
        """Write a register value.

        This may be augmented by the register's side_effect function,
        such as the run register setting the "running" flag.

        Args:
            addr: The register address.
            block_size: The block size to write.
            data: The new register value.

        """
        if len(data) > 1:
            # todo: block size more than one doesnt work here
            raise NotImplementedError()
        # write - dont return anything in response
        self.log.debug("write received - addr:%s block size:%s data:%s ", addr, block_size, data)
        if self.device.registers.get(addr) is not None:
            reg = self.device.registers.get(addr)
            if reg.side_effect is not None:
                value_after_side_effect = reg.side_effect(data[0])
                self.log.debug(
                    "setting %s to %s after side effect from original value %s",
                    addr,
                    value_after_side_effect,
                    data,
                )
                reg.value = reg.side_effect(value_after_side_effect)
            else:
                self.log.debug("setting %s to %s", addr, data)
                reg.value = data[0]
            return
        else:
            self.log.error("invalid write address %s", addr)
            return


def start_emulator(config: ControlConfig) -> None:
    """Start the streaming control board lewis emulator.

    Args:
        config: The main program configuration.

    """
    interface = SCBInterface()
    device = SCBDevice()
    interface.device = device
    for reg_id, reg_addr in config.register_map.items():
        match reg_id:
            case Registers.RUNNING_REGISTER:

                def side_effect(x: int) -> int:
                    return (
                        x | RunRegister.STATUS_RUNNING
                        if x & RunRegister.ETHERNET_OVERRIDE
                        else x & ~RunRegister.STATUS_RUNNING
                    )
            case _:
                side_effect = None
        device.registers[reg_addr] = Register(reg_id, 0, side_effect)
    adapter = interface.adapter(
        options={"bind_address": str(config.board_ip), "port": config.read_port}
    )
    adapter.interface = interface
    s = Simulation(device=device, adapters=[adapter])
    s.start()
