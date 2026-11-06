"""Prometheus-scrapable metrics exposed by `KDAECTRL`."""

from typing import get_args

from prometheus_client import Counter, Gauge, Summary

from kafka_dae_control.worker_event_types import WorkerEvent

_NAMESPACE = "kdaectrl"

HARDWARE_POLL_FAILURES = Counter(
    name="hardware_poll_failures",
    documentation="Number of failed hardware polls",
    namespace=_NAMESPACE,
)

HARDWARE_SETPOINT_FAILURES = Counter(
    name="hardware_setpoint_failures",
    documentation="Number of times a hardware setpoint change failed",
    namespace=_NAMESPACE,
)

HARDWARE_COMMS_OK = Gauge(
    name="hardware_comms_ok",
    documentation="Whether the most recent poll for hardware status succeeded",
    namespace=_NAMESPACE,
)

HARDWARE_POLL_TIME = Summary(
    name="hardware_poll_duration_seconds",
    documentation="Time spent communicating with hardware over UDP to poll for current status",
    namespace=_NAMESPACE,
)

HARDWARE_COMMS_IP_RESETS_ATTEMPTED = Counter(
    name="hardware_comms_ip_resets_attempted",
    documentation="Number of times the comms IP was attempted to be resent to the board",
    namespace=_NAMESPACE,
)

HARDWARE_COMMS_IP_RESETS_SUCCESS = Counter(
    name="hardware_comms_ip_resets_success",
    documentation="Number of times the comms IP was successfully resent to the board",
    namespace=_NAMESPACE,
)

BEGIN_RUN_FAILURES = Counter(
    name="begin_run_failures",
    documentation="Number of failed begin-run operations",
    namespace=_NAMESPACE,
)

END_RUN_FAILURES = Counter(
    name="end_run_failures",
    documentation="Number of failed end-run operations",
    namespace=_NAMESPACE,
)

STATIC_PV_UPDATE_TIME = Summary(
    name="static_pv_update_duration_seconds",
    documentation="Amount of time spent updating static PVs via p4p",
    namespace=_NAMESPACE,
)

STATIC_PV_UPDATE_FAILURES = Counter(
    name="static_pv_update_failures",
    documentation="Number of failed static PV updates",
    namespace=_NAMESPACE,
)

UNHANDLED_WORKER_EVENT_FAILURES = Counter(
    name="unhandled_worker_event_failures",
    documentation="Number of failed unhandled worker event exceptions",
    namespace=_NAMESPACE,
)

WORKER_BUSY = Gauge(
    name="worker_busy",
    documentation="Whether the main-thread worker is currently busy",
    labelnames=["event_type"],
    namespace=_NAMESPACE,
)

for worker_event_type in get_args(WorkerEvent):
    WORKER_BUSY.labels(event_type=worker_event_type.__name__).set(0)

WORKER_BUSY_DURATION = Summary(
    name="worker_busy_duration_seconds",
    documentation="Time spent by the main-thread worker",
    namespace=_NAMESPACE,
)

QUEUE_DEPTH = Gauge(
    name="depth",
    documentation="Number of items on the worker queue",
    namespace=_NAMESPACE,
    subsystem="queue",
)

RUN_CONTROL_UPDATES = Counter(
    name="run_control_updates",
    documentation="Number of times the EPICS run control callback was invoked",
    namespace=_NAMESPACE,
)

BLOCK_NAME_UPDATES = Counter(
    name="block_name_updates",
    documentation="Number of times the EPICS block names callback was invoked",
    namespace=_NAMESPACE,
)

HWSTATUS_RUNNING = Gauge(
    name="running",
    documentation="Whether the streaming hardware is running.",
    namespace=_NAMESPACE,
    subsystem="hwstatus",
)

HWSTATUS_NUM_PERIODS = Gauge(
    name="num_periods",
    documentation="Number of periods configured on the hardware",
    namespace=_NAMESPACE,
    subsystem="hwstatus",
)

HWSTATUS_CURRENT_PERIOD = Gauge(
    name="current_period",
    documentation="Current period configured on the hardware",
    namespace=_NAMESPACE,
    subsystem="hwstatus",
)

HWSTATUS_FRAME_SYNC_SOURCE = Gauge(
    name="frame_sync_source",
    documentation="Frame sync source configured on the hardware",
    namespace=_NAMESPACE,
    subsystem="hwstatus",
)

RUN_NUMBER = Gauge(
    name="run_number",
    documentation="The run number",
    namespace=_NAMESPACE,
)

HWSTATUS_FRAME_SYNC_DELAY = Gauge(
    name="frame_sync_delay",
    documentation="Current frame sync delay configured on the hardware",
    namespace=_NAMESPACE,
    subsystem="hwstatus",
)

KAFKA_DELIVERY_FAILURES = Counter(
    name="delivery_failures",
    documentation="Number of messages which failed to be sent to Kafka",
    namespace=_NAMESPACE,
    subsystem="kafka",
)

KAFKA_DELIVERY_SUCCESS = Counter(
    name="delivery_success",
    documentation="Number of messages which were successfully sent to Kafka",
    namespace=_NAMESPACE,
    subsystem="kafka",
)
