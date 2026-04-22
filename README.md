# kafka_dae_control

This is an IOC in the data streaming stack with two main responsibilities: 

1) Communicate to the FPGA-based streaming hardware and control it, providing an EPICS interface to do so
2) Send [run starts](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/pl72_run_start.fbs) and [stops](https://github.com/ISISComputingGroup/streaming-data-types/blob/master/schemas/6s4t_run_stop.fbs) to Kafka.
