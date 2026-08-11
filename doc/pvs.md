# PVs

This page describes the data held by each PV served by this IOC.

## `BEGINRUNEX`

This is used for starting a run.

Setting this PV to `1` triggers an event which firstly starts the hardware by setting the run status register's lowest bit to 1, then sends a [run start](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) to Kafka. If either of those two fail, the put will error. 

## `ENDRUN`

This is used for ending a run.

Setting this PV to `1` triggers an event which firstly stops the hardware by setting the run status register's lowest bit to 0, then sends a [run stop](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs) to Kafka. If either of those two fail, the put will error.


## `PAUSERUN`

This is used for pausing a run. 

Setting this PV to `1` triggers an event which sets the `software_vetoes` (todo: link this) bit `5` to 1.

## `RESUMERUN`

This is used for resuming a run. 

Setting this PV to `1` triggers an event which sets the `software_vetoes` (todo: link this) bit `5` to 0.

## `DAETIMINGSOURCE` / `DAETIMINGSOURCE:SP`

These PVs respectively display the status of and set the streaming control board's timing source (or `frame_sync_select` as named by its register)
The options are:
- `INTERNAL_TEST_CLOCK`: The streaming control board uses it's internal clock to mark the beginning of new frames, without synchronizing with any external signals. This is useful for testing when an external timing source is not present, but is not useful for scientific data collections.
- `ISIS`: This synchronizes with the ISIS accelerator timing pulse.
- `SMP`: This synchronizes to an external timing pulse, usually from a chopper.
- `UNKNOWN`: The timing source is unknown – the hardware is in a strange state.

## `HWRUNNING`

This PV indicates whether the hardware is running or not, as determined by the status register (in particular the `0x20` bit-flag)

## `RUNNUMBER` / `IRUNNUMBER`

These are the current run number. A run stop increments these. They are read-only from EPICS, but changing the {ref}`statefile` can update them. 

## `PERIOD` / `PERIOD:SP`

The current period number. This is 1-indexed, so period 1 here corresponds to `period=0` in the underlying data stream.

## `NUMPERIODS`/ `NUMPERIODS:MAX` / `NUMPERIODS:SP`

The maximum period number - note that `NUMPERIODS:MAX` is just an alias to `NUMPERIODS`

## `PERIODTYPE` / `PERIODTYPE:SP`

The current period mode to use. Options are: 
`0`/`COMPUTER`: Let the control PC (IBEX) set the period modes
`1`/`LOOK_UP_TABLE`: Internal period card mode, with a look-up table 
`2`/`NOT_USED`: Periods not used at all
`3`/`EXTERNAL`: Use an external signal to the streaming hardware. 

## `VETO:NAMES`
Array of veto names, corresponding to the veto bit mask. Note that this is not changeable at runtime and must be set in the program's configuration file.

## `VETO:SP`
Veto configuration array. This corresponds to the veto names array. The values in this array are `0` for a disabled veto, `1` for a soft veto and `2` for a hard veto.
Setting this will write hard vetoes to hardware and then pushes a [`vc00`](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/vc00_veto_configuration.fbs) blob, containing a bit-wise `OR` of both soft and hard vetoes into the veto configuration topic.

## `VETO:HARD`

This is a readback for what is currently set on the streaming control board.


