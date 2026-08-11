"""Static PVs for KDAECTRL."""

import logging
from queue import PriorityQueue, Queue

from p4p.nt import NTEnum, NTScalar
from p4p.server import ServerOperation, StaticProvider
from p4p.server.thread import SharedPV

from kafka_dae_control.data import Data
from kafka_dae_control.defaults import FrameSyncSelect, PeriodMode
from kafka_dae_control.event_with_error import EventWithError
from kafka_dae_control.queue_utils import QueueItem, QueuePriority
from kafka_dae_control.worker_event_types import (
    BeginEvent,
    CurrentPeriodSetEvent,
    EndEvent,
    FrameSyncSelectChangeEvent,
    NumberOfPeriodsSetEvent,
    PauseResumeEvent,
    PeriodModeSetEvent,
    VetoesUpdateEvent,
    WorkerEvent,
)

logger = logging.getLogger(__name__)


class StaticPVs:
    """Static PVs for KDAECTRL."""

    def __init__(self, data: "Data", queue: PriorityQueue[QueueItem]) -> None:  # ruff:ignore[too-many-statements]
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
                "index": data.frame_sync_select_rbv,
            },
        )
        self.frame_sync_select_sp = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [x.name for x in FrameSyncSelect],
                "index": data.frame_sync_select_sp,
            },
        )
        self.begin = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.end = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.pause = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.resume = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
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
        self.vetoes = SharedPV(
            nt=NTScalar("al", display=True, form=True),
            initial={
                "value": data.vetoes,
                "display.units": "",
                "display.precision": 0,
            },
        )
        self.hard_vetoes_rbv = SharedPV(
            nt=NTScalar("l", display=True, form=True),
            initial={
                "value": data.hard_vetoes_rbv,
                "display.units": "",
                "display.precision": 0,
            },
        )

        self.num_periods_sp = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.num_periods_sp}
        )
        self.num_periods_rbv = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.num_periods_sp}
        )
        self.period_sp = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.current_period_sp}
        )
        self.period_rbv = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.current_period_sp}
        )
        self.period_type_rbv = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [x.name for x in PeriodMode],
                "index": data.period_mode_rbv,
            },
        )
        self.period_type_sp = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [x.name for x in PeriodMode],
                "index": data.period_mode_sp,
            },
        )

        @self.begin.put  # pragma: no cover
        def begin_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("begin")
            ev = EventWithError()
            queue.put(QueueItem(QueuePriority.HIGH, BeginEvent(done_event=ev)))
            try:
                ev.wait()
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to begin: {e}")

        @self.end.put  # pragma: no cover
        def end_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("end")
            ev = EventWithError()
            queue.put(QueueItem(QueuePriority.HIGH, EndEvent(done_event=ev)))
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
            queue.put(
                QueueItem(
                    QueuePriority.HIGH,
                    FrameSyncSelectChangeEvent(value=FrameSyncSelect[str(value)], done_event=ev),
                )
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set frame_sync_select_sp: {e}")

        @self.vetoes.put
        def vetoes_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to vetoes sp", value)
            ev = EventWithError()
            queue.put(QueueItem(QueuePriority.HIGH, VetoesUpdateEvent(value=value, done_event=ev)))
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set soft_vetoes: {e}")

        @self.num_periods_sp.put
        def num_periods_sp_put(pv: SharedPV, op: ServerOperation) -> None:
            value = int(op.value())
            logger.info("put with %s to num_periods_sp", value)
            ev = EventWithError()
            queue.put(
                QueueItem(QueuePriority.HIGH, NumberOfPeriodsSetEvent(value=value, done_event=ev))
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set num_periods_sp: {e}")

        @self.period_sp.put
        def period_sp_put(pv: SharedPV, op: ServerOperation) -> None:
            value = int(op.value())
            logger.info("put with %s to period_sp", value)
            if value < 1:
                op.done(error="Period must be greater than 0")
                return
            ev = EventWithError()
            queue.put(
                QueueItem(QueuePriority.HIGH, CurrentPeriodSetEvent(value=value, done_event=ev))
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set period_sp: {e}")

        @self.period_type_sp.put
        def period_type_sp_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to period_sp", value)
            ev = EventWithError()
            queue.put(
                QueueItem(
                    QueuePriority.HIGH,
                    PeriodModeSetEvent(value=PeriodMode[str(value)], done_event=ev),
                )
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to set period_sp: {e}")

        @self.pause.put
        def pause_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to pause", value)
            ev = EventWithError()
            queue.put(
                QueueItem(
                    QueuePriority.HIGH,
                    PauseResumeEvent(value=True, done_event=ev),
                )
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to pause: {e}")

        @self.resume.put
        def resume_put(pv: SharedPV, op: ServerOperation) -> None:
            value = op.value()
            logger.info("put with %s to resume", value)
            ev = EventWithError()
            queue.put(
                QueueItem(
                    QueuePriority.HIGH,
                    PauseResumeEvent(value=False, done_event=ev),
                )
            )
            try:
                ev.wait()
                pv.post(value)
                op.done()
            except Exception as e:  # ruff:ignore[blind-except]
                op.done(error=f"Failed to resume: {e}")

    def update_all(self, data: Data) -> None:
        """Post updates to all PVs using the data class values.

        Args:
            data: the data class containing the state of the program.

        """
        self.run_number.post(str(data.run_number))
        self.i_run_number.post(data.run_number)
        self.hw_running.post(data.running)
        self.frame_sync_select_rbv.post(data.frame_sync_select_rbv.value)
        self.hard_vetoes_rbv.post(data.hard_vetoes_rbv)
        self.frame_sync_select_rbv.post(data.frame_sync_select_rbv)
        self.num_periods_rbv.post(data.num_periods_rbv)
        self.period_rbv.post(data.current_period_rbv)
        self.period_type_rbv.post(data.period_mode_rbv.name)


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
    static_provider.add(f"{prefix}PAUSERUN", static_pvs.pause)
    static_provider.add(f"{prefix}RESUMERUN", static_pvs.resume)
    static_provider.add(f"{prefix}RUNNUMBER", static_pvs.run_number)
    static_provider.add(f"{prefix}IRUNNUMBER", static_pvs.i_run_number)
    static_provider.add(f"{prefix}DAETIMINGSOURCE", static_pvs.frame_sync_select_rbv)
    static_provider.add(f"{prefix}DAETIMINGSOURCE:SP", static_pvs.frame_sync_select_sp)
    static_provider.add(f"{prefix}VETO:NAMES", static_pvs.veto_names_array)
    static_provider.add(f"{prefix}VETO:SP", static_pvs.vetoes)
    static_provider.add(f"{prefix}VETO:HARD", static_pvs.hard_vetoes_rbv)
    static_provider.add(f"{prefix}NUMPERIODS:MAX", static_pvs.num_periods_sp)
    static_provider.add(f"{prefix}NUMPERIODS:SP", static_pvs.num_periods_sp)
    static_provider.add(f"{prefix}NUMPERIODS", static_pvs.num_periods_rbv)
    static_provider.add(f"{prefix}PERIOD", static_pvs.period_rbv)
    static_provider.add(f"{prefix}PERIOD:SP", static_pvs.period_sp)
    static_provider.add(f"{prefix}PERIODTYPE", static_pvs.period_type_rbv)
    static_provider.add(f"{prefix}PERIODTYPE:SP", static_pvs.period_type_sp)
    return static_pvs, static_provider
