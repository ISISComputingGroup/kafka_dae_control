"""Data class containing the state of the program."""

import logging
import socket
from collections.abc import Callable
from typing import TypeVar

from attr import Factory
from attrs import define, field

from kafka_dae_control.run_state import RunState

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ObservableField[T]:
    """A wrapper around a value which allows callbacks to be called when it's value has changed."""

    def __init__(self, value: T = None) -> None:
        """Initialise the ObservableField.

        Args:
            value: the initial value.

        """
        self.callbacks = []
        self._value = value

    def attach(self, cb: Callable[[T, T], None]) -> None:
        """Attach a callback which will be called when it's value has changed.

        The signature will be `cb(old_value, new_value)`

        Args:
            cb: the callback to be called.

        Returns: None

        """
        self.callbacks.append(cb)

    @property
    def value(self) -> T:
        """The current value of the observable.

        Returns: the current value.

        """
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """Set a new value and call the callbacks attached.

        Args:
            value: the new value to be set.

        Returns: None

        """
        old_val = self.value
        self._value = value
        logger.debug("set value for pv to %s", value)
        for callback in self.callbacks:
            callback(old_val, value)


@define
class Data:
    """A mutable object describing the data being served by this IOC."""

    running: ObservableField[bool] = field(  # pyright: ignore [reportAssignmentType]
        converter=ObservableField, default=False
    )  # hardware is running
    run_state: ObservableField[RunState] = field(  # pyright: ignore [reportAssignmentType]
        converter=ObservableField, default=RunState.SETUP
    )  # run state of KDAECTRL - this may differ from running

    title: ObservableField[str] = field(converter=ObservableField, default="")  # pyright: ignore [reportAssignmentType]
    users: ObservableField[str] = field(converter=ObservableField, default="")  # pyright: ignore [reportAssignmentType]
    job_id: ObservableField[str] = field(converter=ObservableField, default="")  # pyright: ignore [reportAssignmentType]
    run_number: ObservableField[int] = field(converter=ObservableField, default=0)  # pyright: ignore [reportAssignmentType]
    blocks: list[str] = Factory(  # pyright: ignore [reportAssignmentType]
        list
    )  # not observable - we aren't catering for if blocks change mid-run
    instrument_name: str = field(  # pyright: ignore [reportAssignmentType]
        default=socket.gethostname()
    )  # not observable - this shouldn't really change ever
