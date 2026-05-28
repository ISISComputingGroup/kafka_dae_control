# PVs

This page describes the data held by each PV served by this IOC.

## `BEGINRUNEX`

This is used for starting a run.

Setting this PV to `1` triggers an event which firstly starts the hardware by setting the run status register's lowest bit to 1, then sends a [run start](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) to Kafka. If either of those two fail, the put will error. 

## `ENDRUN`

This is used for ending a run.

Setting this PV to `1` triggers an event which firstly stops the hardware by setting the run status register's lowest bit to 0, then sends a [run stop](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs) to Kafka. If either of those two fail, the put will error.

## `DAETIMINGSOURCE` / `DAETIMINGSOURCE:SP`

These PVs respectively display the status of and set the streaming control board's timing source (or `frame_sync_select` as named by its register)

## `HWRUNNING`

This PV indicates whether the hardware is running or not, as determined by the status register (in particular the `0x20` bit-flag)

## `TITLE` / `USERS`

These are just "soft" PVs used for forming the [run starts](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) and [stops](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs)


## `RUNNUMBER` / `IRUNNUMBER`

These are the current run number. A run stop increments these. They are read-only from EPICS, but changing the {ref}`statefile` can update them. 
