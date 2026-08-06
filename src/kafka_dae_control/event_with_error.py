"""Module containing utilities for passing events between threads with an exception."""

import threading


class EventWithError(threading.Event):
    """A wrapper around a threading.Event which can hold an exception.

    This can be used for determining the success or failure (respectively) of the event.
    """

    def __init__(self) -> None:
        """Create the event object."""
        super().__init__()
        self._err = None

    def wait(self, timeout: float | None = None) -> bool:
        """Wait for the event to be set.

        Either return after waiting, or raise if there is an exception.

        """
        res = super().wait(timeout)
        if self._err is not None:
            raise self._err
        return res

    @property
    def err(self) -> Exception | None:
        """The exception.

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
        self.set()
