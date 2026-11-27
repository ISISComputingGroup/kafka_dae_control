from time import sleep
from dataclasses import dataclass
from typing import Callable

from lewis.adapters.stream import Cmd
from lewis.adapters.udp import UDPInterface
from lewis.core.logging import has_log
from lewis.core.simulation import Simulation
from lewis.devices import Device

from kafka_dae_control.config import ControlConfig
from kafka_dae_control.defaults import Registers, RunRegister


@dataclass
class Register:
    name: str
    """The register `id` from the firmware xml"""
    value: int
    """The current register value"""
    side_effect: Callable[[int], int] | None = None
    """A side effect to call on the current value when set. input argument is the new value, output is the new value with whatever side effect has been applied to it"""


class SCBDevice(Device):
    registers: dict[int, Register] = {}
    """mapping of address - name/value"""


@has_log
class SCBInterface(UDPInterface):
    commands = {Cmd("command", pattern="(.*)", return_mapping=None)}

    def command(self, data: bytes) -> int | None:
        """Main command for the streaming control board.
        This follows the same protocol as the real device, which is
        documented here: https://isiscomputinggroup.github.io/kafka_dae_control/local_development.html#sending-reading-data-to-from-the-hardware

        For a register read this is a 32 bit int of the address to read + a 16 bit int of the block size (in words)

        for a register write this is a 32 bit int of the address to read + a 16 bit int of the block size (in words) + 32 bit int of the data to write

        Every register on the board is just 1 word, so the 16 bit int never changes - it's always 1.

        """
        addr = int.from_bytes(data[:4], byteorder="big")

        # parse the 16-bit block size
        block_size = int.from_bytes(data[4:6], byteorder="big")
        written_data = (
            int.from_bytes(data[6 : 6 + (block_size * 4)], byteorder="big")
            if len(data[6:]) > 0
            else None
        )
        self.log.debug(
            f"command received:{data} - addr:{addr} block size:{block_size} is write:{written_data is not None} {f' written data:{written_data}' if written_data is not None else ''} "
        )

        # todo this is not complete - some side effects need to occur like setting the run registers lsb(?) to 1 if we've just requested a run
        if written_data is not None:
            # write - dont return anything in response
            if self.device.registers.get(addr) is not None:
                reg = self.device.registers.get(addr)
                if reg.side_effect is not None:
                    value_after_side_effect = reg.side_effect(written_data)
                    self.log.debug(f"setting {addr} to {value_after_side_effect} after side effect from original value {written_data}")
                    reg.value = reg.side_effect(value_after_side_effect)
                else:
                    self.log.debug(f"setting {addr} to {written_data}")
                    reg.value = written_data
                return None
            else:
                self.log.error(f"invalid write address {addr}")
                return None
        else:
            # read - return the address, block size and read data
            if addr in self.device.registers:
                val = self.device.registers[addr].value
                self.log.debug(f"read {val} from {addr}")
                to_return =  (
                    addr.to_bytes(4, byteorder="big")
                    + block_size.to_bytes(2, byteorder="big")
                    + val.to_bytes(block_size * 4, byteorder="big")
                )
                self.log.debug(f"Returning {to_return}")
                return to_return
            else:
                self.log.error(f"invalid read address {addr}")
                return None

    def handle_error(self, request, error):
        self.log.info(f"error: {error}")
        return "An error occurred: " + repr(error)


def start_emulator(config: ControlConfig) -> None:
    print("Starting emulator...")
    interface = SCBInterface()
    device = SCBDevice()
    interface.device = device
    for reg_id, reg_addr in config.register_map.items():
        match reg_id:
            case Registers.RUNNING_REGISTER:
                side_effect = lambda x: x | RunRegister.STATUS_RUNNING if x & RunRegister.ETHERNET_OVERRIDE else x &~ RunRegister.STATUS_RUNNING
            case _:
                side_effect = None
        device.registers[reg_addr] = Register(
            reg_id, 0, side_effect
        )
    adapter = interface.adapter(
        options={"bind_address": str(config.board_ip), "port": config.read_port}
    )
    adapter.interface = interface
    s = Simulation(device=device, adapters=[adapter])
    s.start()
    print("Emulator started")
