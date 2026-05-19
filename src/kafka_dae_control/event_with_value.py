"""Module containing utilities for passing events between threads with an exception or value."""

import threading


class EventWithValue[T]:
    """A wrapper around a threading.Event which can hold a value or exception.

    This can be used for determining the success or failure (respectively) of the event.
    """

    def __init__(self) -> None:
        """Create the event object."""
        self._ev = threading.Event()
        self._value = None
        self._err = None

    def wait(self) -> T | None:
        """Wait for the event to be set.

        Either return the current value if there is one, or raise if there is an exception.

        Returns: The current value if there is one.

        """
        self._ev.wait()
        if self._err is not None:
            raise self._err
        return self._value

    def set(self) -> None:
        """Directly set on the event."""
        self._ev.set()

    @property
    def value(self) -> T | None:
        """The value.

        Returns: The value.

        """
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """Set the value and call set() on the event. This halts a wait.

        Args:
            value: The new value to set

        """
        self._value = value
        self._ev.set()

    @property
    def err(self) -> Exception | None:
        """Get the exception.

        Returns: The exception.

        """
        return self._err

    @err.setter
    def err(self, err: Exception) -> None:
        """Set the exception and call set() on the event. This halts a wait.

        Args:
            err: the exception to set.

        """
        self._err = err
        self._ev.set()
