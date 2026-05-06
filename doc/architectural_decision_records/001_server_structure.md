# 1. EPICS Server structure

## Status

Current

## Context

This module's responsibility is to:
1) Communicate with the streaming control boards in the data streaming pipeline
2) Send [run starts](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) and [stops](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs) to a Kafka topic for downstream consumers to know that a run has started or stopped.
3) Serve an EPICS IOC to allow doing the above via EPICS with a similar interface to `ISISDAE` currently used to communicate to the previous detector acquisition electronics.

All of this _could_ be achieved with an EPICS StreamDevice IOC along with state notation language or similar for the run state. This is one option. 

The IOC part of this can be achieved with several options: 

### Channel Access
[`caproto`](https://discussions.apple.com/thread/255775451?sortBy=rank) is an option to use Channel Access as a server, however it is [not currently maintained](https://github.com/caproto/caproto/issues/786)

[`pcaspy`](https://pcaspy.readthedocs.io/en/latest/) is another option, but it uses the `PCAS` library which is also deprecated - it's no longer bundled in EPICS releases.

Channel Access is now generally a legacy protocol which is not recommended for new development.

### PV Access
[`p4p`](https://epics-base.github.io/p4p/index.html) is the de-facto library to use for PV access in python, and is actively maintained.

### Both
[`FastCS`](https://github.com/DiamondLightSource/FastCS) can provide a way of writing EPICS device support with a PV Access and Channel Access server simultaneously.

This project is still fairly early in development, and documentation is somewhat sparse. It would also need UDP support (and the streaming control board's protocol) for this particular use case.

## Decision 

The IOC will be written in Python as it is much easier for rapid prototyping and can more easily be separated from the rest of the EPICS build as it doesn't require a compiled state-notation language support module or asyn/streamDevice.

The IOC will use {py:obj}`p4p`'s {py:obj}`server API <p4p.server.Server>` and will serve PV Access only.

## Consequences
- PVs will only be available via PV Access. The GUI and any other clients eg. `genie-python` will need to cater for this.
  - Clients like `genie-python` will need to cater for certain pieces of logic being different anyway.
- The IOC will serve PVs using the {py:obj}`p4p.server.Server` API.
