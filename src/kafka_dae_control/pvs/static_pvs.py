"""Static PVs for KDAECTRL."""

import logging
from queue import Queue

from p4p.nt import NTEnum, NTScalar
from p4p.server import ServerOperation, StaticProvider
from p4p.server.thread import SharedPV

from kafka_dae_control.data import Data
from kafka_dae_control.defaults import FrameSyncSelect
from kafka_dae_control.event_with_error import EventWithError
from kafka_dae_control.worker_event_types import (
    BeginEvent,
    EndEvent,
    FrameSyncSelectChangeEvent,
    HardVetoesUpdateEvent,
    SoftVetoesUpdateEvent,
    WorkerEvent,
)

logger = logging.getLogger(__name__)


class StaticPVs:
    """Static PVs for KDAECTRL."""

    def __init__(self, data: "Data", queue: Queue[WorkerEvent]) -> None:  # ruff:ignore [too-many-statements]
        """Set up static PVs for KDAECTRL.

        Args:
            data: the data class containing the state of the program.
            queue: the worker event queue.

        """
        self.hw_running = SharedPV(
            nt=NTScalar(display=True, form=True),
            initial={
                "value": data.running,
            },
        )
        self.frame_sync_select_rbv = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [x.name for x in FrameSyncSelect],
                "index": data.frame_sync_select_rbv.value,
            },
        )
        self.frame_sync_select_sp = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [x.name for x in FrameSyncSelect],
                "index": data.frame_sync_select_sp.value,
            },
        )
        self.begin = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.end = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.run_number = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": str(data.run_number)}
        )
        self.i_run_number = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.run_number}
        )
        self.veto_names_array = SharedPV(
            nt=NTScalar("as", display=True, form=True),
            initial={
                "value": data.veto_names_array,
            },
        )
        self.soft_vetoes = SharedPV(
            nt=NTScalar("al", display=True, form=True),
            initial={
                "value": data.soft_vetoes_array,
                "display.units": "",
                "display.precision": 0,
            },
        )
        self.hard_vetoes_sp = SharedPV(
            nt=NTScalar("al", display=True, form=True),
            initial={
                "value": data.soft_vetoes_array,
                "display.units": "",
                "display.precision": 0,
            },
        )
        self.hard_vetoes_rbv = SharedPV(
            nt=NTScalar("al", display=True, form=True),
            initial={
                "value": data.soft_vetoes_array,
                "display.units": "",
                "display.precision": 0,
            },
        )

        @self.begin.put  # pragma: no cover
        def begin_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("begin")
            ev = EventWithError()
            queue.put(BeginEvent(done_event=ev))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to begin: {e}")

        @self.end.put  # pragma: no cover
        def end_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("end")
            ev = EventWithError()
            queue.put(EndEvent(done_event=ev))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to end: {e}")

        @self.frame_sync_select_sp.put
        def frame_sync_select_sp_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to frame_sync_select_sp", value)
            ev = EventWithError()
            queue.put(FrameSyncSelectChangeEvent(value=FrameSyncSelect(value), done_event=ev))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set frame_sync_select_sp: {e}")

        @self.soft_vetoes.put
        def soft_vetoes_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to soft_vetoes", value)
            ev = EventWithError()
            queue.put(SoftVetoesUpdateEvent(value=value, done_event=ev))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set soft_vetoes: {e}")

        @self.hard_vetoes_sp.put
        def hard_vetoes_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to soft_vetoes", value)
            ev = EventWithError()
            queue.put(HardVetoesUpdateEvent(value=value, done_event=ev))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set soft_vetoes: {e}")

    def update_all(self, data: Data) -> None:
        """Post updates to all PVs using the data class values.

        Args:
            data: the data class containing the state of the program.

        """
        self.run_number.post(str(data.run_number))
        self.i_run_number.post(data.run_number)
        self.hw_running.post(data.running)
        self.frame_sync_select_rbv.post(data.frame_sync_select_rbv.value)


def static_pv_provider(
    pv_prefix: str, data: "Data", queue: Queue[WorkerEvent]
) -> tuple[StaticPVs, StaticProvider]:
    """Generate a static pv provider containing all the static PVs.

    This also sets up basic post hooks for observable dataclass items.

    Args:
        pv_prefix: the PV prefix.
        data: The data class containing the state of the program.
        queue: the worker event queue.

    Returns: A static pv provider containing static PVs.

    """
    static_pvs = StaticPVs(data, queue)
    static_provider = StaticProvider()
    dae_prefix = "DAE:"
    prefix = f"{pv_prefix}{dae_prefix}"
    static_provider.add(f"{prefix}HWRUNNING", static_pvs.hw_running)
    static_provider.add(f"{prefix}BEGINRUNEX", static_pvs.begin)
    static_provider.add(f"{prefix}ENDRUN", static_pvs.end)
    static_provider.add(f"{prefix}RUNNUMBER", static_pvs.run_number)
    static_provider.add(f"{prefix}IRUNNUMBER", static_pvs.i_run_number)
    static_provider.add(f"{prefix}DAETIMINGSOURCE", static_pvs.frame_sync_select_rbv)
    static_provider.add(f"{prefix}DAETIMINGSOURCE:SP", static_pvs.frame_sync_select_sp)
    static_provider.add(f"{prefix}VETO:NAMES", static_pvs.veto_names_array)
    static_provider.add(f"{prefix}VETO:HARD:SP", static_pvs.hard_vetoes_sp)
    static_provider.add(f"{prefix}VETO:HARD", static_pvs.hard_vetoes_sp)
    static_provider.add(f"{prefix}VETO:SOFT:SP", static_pvs.soft_vetoes)
    return static_pvs, static_provider
