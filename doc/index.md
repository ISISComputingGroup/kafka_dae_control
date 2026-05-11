# Kafka DAE Control

This module provides the `KDAECTRL` IOC, which acts as a bridge between EPICS and the streaming control boards used to control the data acquisition hardware.

It serves as a state machine for the run state and pushes [run starts](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) and [stops](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs) to a Kafka topic.

---

```{toctree}
:titlesonly:
:caption: Developer Information
:glob:

local_development
architectural_decision_records
threads
```

```{toctree}
:titlesonly:
:caption: Reference
:glob:

_api
```