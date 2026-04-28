"""The main entrypoint for the KDAECTRL IOC."""

import argparse
import logging
import os

from kafka_dae_control.config import load_config
from kafka_dae_control.serve import serve

# needed for p4p and pyepics to work together
try:
    import epicscorelibs.path.pyepics  # noqa: F401
except ImportError:
    pass
import sys

logger = logging.getLogger(__name__)


def main() -> None:
    """Run the IOC."""
    if "EPICS_CA_ADDR_LIST" not in os.environ:
        logger.error("EPICS_CA_ADDR_LIST not set")
        sys.exit(1)
    if "EPICS_PVAS_INTF_ADDR_LIST" not in os.environ:
        logger.error("EPICS_PVAS_INTF_ADDR_LIST not set")
        sys.exit(1)

    ap = argparse.ArgumentParser(
        description="KDAECTRL - Kafka-dae-control",
        epilog="This relies on EPICS environment variables. These are:"
        "\n\tEPICS_CA_ADDR_LIST: for the blockserver CA PVs"
        "\n\tEPICS_PVAS_INTF_ADDR_LIST: the interface to bind to for PVA",
    )
    ap.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to config file.",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level.",
    )
    args = ap.parse_args()

    logging.basicConfig(level=args.log_level)

    config = load_config(args.config)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    serve(config)
