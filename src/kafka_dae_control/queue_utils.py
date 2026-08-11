"""Types for queue items and priorities."""

import time
from dataclasses import dataclass, field
from enum import IntEnum

from kafka_dae_control.worker_event_types import WorkerEvent


class QueuePriority(IntEnum):
    """Priority levels for queue items."""

    HIGH = 1
    LOW = 2


@dataclass(order=True)
class QueueItem:
    """A queue item with a priority."""

    priority: QueuePriority
    item: WorkerEvent = field(compare=False)
    time: float = field(default_factory=time.time)
