"""Static PVs for KDAECTRL."""

import logging

from p4p._p4p import ServerOperation
from p4p.nt import NTEnum, NTScalar
from p4p.server import StaticProvider
from p4p.server.thread import SharedPV

from kafka_dae_control.data import Data
from kafka_dae_control.run_state import RunState

logger = logging.getLogger(__name__)


class StaticPVs:
    """Static PVs for KDAECTRL."""

    def __init__(self, data: "Data") -> None:
        """Set up static PVs for KDAECTRL.

        Args:
            data: the data class containing the state of the program.

        """
        self.hw_running = SharedPV(
            nt=NTScalar(display=True, form=True),
            initial={
                "value": data.running.value,
            },
        )
        self.runstate = SharedPV(
            nt=NTEnum(),
            initial={
                "choices": [state.name for state in RunState],
                "index": data.run_state.value.value,
            },
        )
        self.runstate_str = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": data.run_state.value.name}
        )
        self.begin = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.end = SharedPV(nt=NTScalar(display=True, form=True), initial={"value": False})
        self.run_number = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": data.run_number.value}
        )
        self.i_run_number = SharedPV(
            nt=NTScalar(display=True, form=True), initial={"value": data.run_number.value}
        )
        self.title = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": data.title.value}
        )
        self.users = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": data.users.value}
        )
        self.inst_name = SharedPV(
            nt=NTScalar("s", display=True, form=True), initial={"value": data.instrument_name}
        )

        @self.title.put
        def title_put(pv: SharedPV, op: ServerOperation) -> None:
            pv.post(op.value())
            data.title.value = op.value()
            op.done()

        @self.users.put
        def users_put(pv: SharedPV, op: ServerOperation) -> None:
            pv.post(op.value())
            data.users.value = op.value()
            op.done()

        @self.begin.put
        def begin_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("begin")
            data.run_state.value = RunState.BEGINNING
            op.done()

        @self.end.put
        def end_put(_: SharedPV, op: ServerOperation) -> None:
            logger.info("end")
            data.run_state.value = RunState.ENDING
            op.done()


def static_pv_provider(pv_prefix: str, data: "Data") -> StaticProvider:
    """Generate a static pv provider containing all the static PVs.

    This also sets up basic post hooks for observable dataclass items.

    Args:
        pv_prefix: the PV prefix.
        data: The data class containing the state of the program.

    Returns: A static pv provider containing static PVs.

    """
    static_pvs = StaticPVs(data)
    static_provider = StaticProvider()
    dae_prefix = "DAE:"
    prefix = f"{pv_prefix}{dae_prefix}"
    static_provider.add(f"{prefix}HWRUNNING", static_pvs.hw_running)
    static_provider.add(f"{prefix}BEGINRUNEX", static_pvs.begin)
    static_provider.add(f"{prefix}ENDRUN", static_pvs.end)
    static_provider.add(f"{prefix}TITLE", static_pvs.title)
    static_provider.add(f"{prefix}USERS", static_pvs.users)
    static_provider.add(f"{prefix}RUNSTATE", static_pvs.runstate)
    static_provider.add(f"{prefix}RUNSTATE_STR", static_pvs.runstate_str)
    static_provider.add(f"{prefix}RUNNUMBER", static_pvs.run_number)
    static_provider.add(f"{prefix}IRUNNUMBER", static_pvs.i_run_number)
    data.running.attach(lambda _, x: static_pvs.hw_running.post(x))
    data.run_state.attach(lambda _, x: static_pvs.runstate.post(x.value))
    data.run_state.attach(lambda _, x: static_pvs.runstate_str.post(x.name))
    data.title.attach(lambda _, x: static_pvs.title.post(x))
    data.run_number.attach(lambda _, x: static_pvs.run_number.post(x))
    data.users.attach(lambda _, x: static_pvs.users.post(x))
    return static_provider
