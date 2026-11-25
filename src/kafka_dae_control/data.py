"""Data class containing the state of the program."""

import logging
from typing import Any, Self, TypeVar

from pydantic import BaseModel, Field, RootModel, model_validator
from streaming_data_types.run_start_pl72 import DetectorSpectrumMap

from kafka_dae_control.defaults import NUM_VETOES, FrameSyncSelect, PeriodMode

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SingleDetSpecMapping(BaseModel):
    """A single detector spectrum mapping."""

    det: int = Field(ge=0, le=2**31 - 1)
    spec: int = Field(ge=0, le=2**31 - 1)


class DetectorSpectraMapping(RootModel[list[SingleDetSpecMapping]]):
    """Pydantic model for validating detector-spectra mapping."""

    @model_validator(mode="after")
    def check_detector_ids_are_unique(self) -> Self:
        """Check that the detector IDs are unique.

        Detector IDs cannot be repeated in a detector spectrum mapping.
        """
        dets = set()
        for det, _ in self.root:
            if det not in dets:
                dets.add(det)
            else:
                raise ValueError(f"Detector ID must be unique. Offending ID: {det[1]}")
        return self

    def to_df12_blob(self) -> DetectorSpectrumMap:
        """Construct a DetectorSpectrumMap object from this pydantic model.

        This works out the n_spectra field by finding the maximum spectrum number and adding 1.

        Returns: A mapping object which can be used when serialising a run-start.
        """
        return DetectorSpectrumMap(self.spectra, self.detector_ids, self.n_spectra)

    @property
    def spectra(self) -> list[int]:
        """A list of spectra."""
        return [x.spec for x in self.root]

    @property
    def detector_ids(self) -> list[int]:
        """A list of detector IDs."""
        return [x.det for x in self.root]

    @property
    def n_spectra(self) -> int:
        """Maximum number of spectra, plus 1. If spectra is empty, this returns 1."""
        return max(self.spectra) + 1 if self.spectra else 1


class Data(BaseModel):
    """A mutable object describing the data being served by this IOC.

    This object is only ever mutated by the main worker thread. It is read by
    the main worker thread and the PV update thread.
    """

    running: bool = False
    """Whether the hardware is running or not"""

    paused: bool = False
    """Whether the hardware is paused or not"""

    frame_sync_select_rbv: FrameSyncSelect = FrameSyncSelect.UNKNOWN
    """The frame sync select value on the hardware"""

    frame_sync_select_sp: FrameSyncSelect = FrameSyncSelect.UNKNOWN
    """The frame sync select value setpoint"""

    job_id: str = ""
    """Run's job_id, used to tie starts and stops together"""

    run_number: int = 0
    """Run number"""

    blocks: list[str] = Field(default_factory=list)
    """List of blocks to be inserted in the run start nexus structure.
     These are prefixed with the instrument and block server prefixes"""

    veto_names_array: list[str] = Field(default=[f"veto_{n}" for n in range(NUM_VETOES)])
    """
    Veto names, as a numpy array of strings. This is indexed so that 0 is veto 0.
    """

    vetoes: list[int] = Field(default=[0] * NUM_VETOES)
    """Vetoes array containing 0 for disabled, 1 for soft, 2 for hard.
     This is indexed so that item 0 is veto 0."""

    hard_vetoes_rbv: int = 0xFFFF
    """Hard vetoes readback bit mask"""

    num_periods_sp: int = 1
    """Number of periods (setpoint)."""

    num_periods_rbv: int = 1
    """Number of periods (readback)."""

    current_period_sp: int = 1
    """Current period number setpoint. This is 1-indexed for backwards compatibility reasons."""

    current_period_rbv: int = 1
    """Current period number readback. This is 1-indexed for backwards compatibility reasons."""

    period_mode_sp: PeriodMode = PeriodMode.UNKNOWN
    """The period mode setpoint."""

    period_mode_rbv: PeriodMode = PeriodMode.UNKNOWN
    """The period mode readback."""

    detector_spectrum_mapping: DetectorSpectraMapping = DetectorSpectraMapping.model_validate([])
    """The detector spectrum mapping"""

    frame_sync_delay_sp: int = 0
    """The frame sync delay setpoint (us)."""

    frame_sync_delay_rbv: int = 0
    """The frame sync delay readback (us)."""

    most_recent_run_start_args: dict[str, Any] = {}
    """The arguments for constructing the most recent run-start blob.
     This is used when cancelling an abort to re-send the run start."""

    last_hardware_update_ok: bool = False
    """Whether the most recent hardware update successfully polled the hardware."""
