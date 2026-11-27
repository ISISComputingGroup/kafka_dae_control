from time import sleep
from dataclasses import dataclass
from typing import Callable

from lewis.adapters.stream import Cmd
from lewis.adapters.udp import UDPInterface
from lewis.core.logging import has_log
from lewis.core.simulation import Simulation
from lewis.devices import Device

from kafka_dae_control.config import ControlConfig


@dataclass
class Register:
    name: str
    value: int
    # side_effect: Callable[[int], int]


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
                self.log.debug(f"setting {addr} to {written_data}")
                self.device.registers[addr].value = written_data
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
        device.registers[reg_addr] = Register(
            reg_id, 0
        )  # todo is setting everything to 0 really what we want?
    adapter = interface.adapter(
        options={"bind_address": str(config.board_ip), "port": config.read_port}
    )
    adapter.interface = interface
    s = Simulation(device=device, adapters=[adapter])
    s.start()
    print("Emulator started")
