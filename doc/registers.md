# Streaming control board registers

This page documents the registers on the streaming control board. 

A register is a 32-bit word usually made up of a mask with bit flags. In some cases, for example the `udp_core.udp_core_control_0_dst_ip_addr` register, it is just the big-endian representation of an integer.
These are signified with either "Bits (mask)" or "Value". Values are read-only unless otherwise noted with "(`rw`)". 

These may be differently addressed with different boards/firmware versions, so it is laid out using the register name rather than any fixed address. 

## `run_period_control` prefixed registers

### `run_register`

This register is used for starting/stopping the hardware and monitoring whether it's running or not. 

Bits (mask):
31-6: Unused
5 (`used_run_signal`): Readback for if the board is actually running or not. `1`: running, `0`: not running
4 (`stream_empty_frames`)(`rw`): Toggle for streaming empty frames
3 (`increment_frame_counter_n`)(`rw`): Toggle for incrementing the frame counter even if the run signal is not `1`. `0`: increment counter, `1`: don't increment counter
2, 1 (`run_signal_select`)(`rw`): The run signal select bits. Options: `3`: External run allowing for short pause, `2`: Ethernet run siganl synced to external run signal, `1`: Ethernet run signal, `0`: External run signal
0 (`run_register`)(`rw`): Toggle to start and stop runs. `1`: start, `2`: stop

### `frame_sync_sel`

This register is used for selecting the timing source. Only one option can be set despite it being a mask.

Value `frame_sync_sel`(`rw`): Which timing source to use. Options: `0`: Internal test clock, `1`: SMP, `2`: ISIS

### `internal_frame_period`

The internal frame sync period. 

Value `internal_frame_period`(`rw`): The time in microseconds to use. For example `0x04E20`=`~20ms`,`0x18600`=`~100ms`

### `frame_sync_delay`

Value `frame_sync_delay`(`rw`): Frame Sync time delay from frame source trigger (in microseconds) 

### `run_period_control.fast_chopper_delay_x` / `run_period_control.fast_chopper_width_x`
(all `rw`) where `x` is the fast chopper number. 

### `period_control`

Bits (mask):
31-7: Unused
6 (`period_end_run_last_sequence`)(`rw`): Toggle to end run _after_ the last period sequence
5, 4 (`period_mode`)(`rw`): The period mode to use. Options: `00`: Computer (`kdaectrl` controlled), `01`: Look up table (internal period card), `02`: External signal
3: Unused
2: Unused
1 (`period_end_run_sequence`)(`rw`): Toggle to end run _at_ the end of the period sequence
0: Unused

### `period_comp_current`

Value `period_comp_current`(`rw`): The current period number set by `kdaectrl`.

### `period_number_limit`

Value `period_number_limit`(`rw`): The maximum period number. 

### `period_sequence_limit`

Value `period_sequence_limit`(`rw`): The maximum period sequence number.

### `run_pause_wait_time`

Value `run_pause_wait_time`(`rw`): The amount of time to wait when `run_register` goes to low before stopping the run (to account for pauses).

### `time_correction_enable`

Bits (mask):
31-1: unused
0 (`time_correction_enable`)(`rw`): Toggle to enable firmware that corrects the frame time due to inaccuracy of board oscillators.

### `time_correction_frame_length`

Value `time_correction_frame_length`(`rw`): The frame length for the time correction process, in nanoseconds. `x3B9ACA00=1second (PPS)`, `x01312D00=20ms (TS1)`, `x05F5E100-100ms (TS2)`

### `enable_crc`

Register used to control whether or not the status packet uses a CRC check.

Bits (mask): 
31-2: Unused
1 (`tx`)(`rw`): Controls if the TX path should perform status packet check
0 (`rx`)(`rw`): Controls if the RX path should perform status packet check

### `crc_error_count`

Value `crc_error_count`: The number of CRC errors detected.

### `crc_present`

Bits (mask):
31-1: Unused
0 (`crc_present`): A single bit flag that shows if a CRC is present.

### `crc_pass`

Bits (mask):
31-1: Unused
0 (`crc_present`): A single bit flag showing if the CRC is correct

### `years`

Value: Current status packet time - years

### `days`

Value: Current status packet time - days

### `hours`

Value: Current status packet time - hours

### `minutes`

Value: Current status packet time - minutes

### `seconds`

Value: Current status packet time - seconds

### `milliseconds`

Value: Current status packet time - milliseconds

### `microseconds`

Value: Current status packet time - microseconds

### `nanoseconds`

Value: Current status packet time - nanoseconds

### `ppp_current_value`

Value: Protons per pulse in the current frame. 

### `period_number`

Value: The current period number.

### `veto_number`

Value: The current veto number.

### `veto_mask`

Bits (mask) (`rw`): The vetos to ignore. 

### `good_frame_count`

Value: Count of the good (non-vetoed) frames in the run.

### `raw_frame_count`

Value: Count of all the frames in the run.

### `ppp_total_count`

Value: Sum of the protons per pulse in the run. 

### `time_since_gps`

Value: The time in microseconds since the last GPS signal was received. 

### `sp_tx_enable`

Bits (mask):
31-1: Unused
0 (`sp_tx_enable`)(`rw`): Toggle to enable the status packet in the UDP stream.

## `firmware_number` prefixed registers 

These are self-describing and describe the board firmware version.

## `fpga_mon_cont` prefixed registers
These are internal registers used to monitor parameters on the FPGA such as temperature.

## `udp_core` prefixed registers
These are mostly related to networking and internal device state. The only one `kdaectrl` uses currently is `udp_core_control_0_dst_ip_addr` which is a big-endian representation of the IPv4 address for the "client", which in the case of `kdaectrl` is the host running it.
