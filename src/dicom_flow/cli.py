import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from dicom_flow.common.config import ReceiverSettings, WorkerSettings
from dicom_flow.common.logging import configure_logging
from dicom_flow.receiver.client import collect_dicom_files, send_instances
from dicom_flow.receiver.server import create_receiver
from dicom_flow.synthetic import create_synthetic_study
from dicom_flow.worker.consumer import run_worker

LOGGER = logging.getLogger(__name__)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dicom-flow")
    commands = parser.add_subparsers(dest="command", required=True)

    generate = commands.add_parser("generate", help="create a synthetic ultrasound study")
    generate.add_argument("--output", type=Path, default=Path("./data/synthetic"))
    generate.add_argument("--instances", type=int, default=2)
    generate.add_argument("--seed", type=int, default=1)

    commands.add_parser("serve", help="run the DICOM C-STORE receiver")
    commands.add_parser("worker", help="run the Redis-backed DICOM processing worker")

    send = commands.add_parser("send", help="C-ECHO and C-STORE DICOM files to a receiver")
    send.add_argument("path", type=Path)
    send.add_argument("--host", default="127.0.0.1")
    send.add_argument("--port", type=int, default=11112)
    send.add_argument("--calling-ae", default="SYNTHETIC_SCU")
    send.add_argument("--called-ae", default="DICOMFLOW")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    configure_logging()
    args = _parser().parse_args(argv)

    if args.command == "generate":
        created = create_synthetic_study(args.output, instances=args.instances, seed=args.seed)
        LOGGER.info("synthetic_study_created: %d instances", len(created))
        return

    if args.command == "serve":
        settings = ReceiverSettings()
        server = create_receiver(settings)
        LOGGER.info("receiver_started on port %d", server.server_address[1])
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            LOGGER.info("receiver_stopping")
            server.shutdown()
        return

    if args.command == "worker":
        run_worker(WorkerSettings())
        return

    files = collect_dicom_files(args.path)
    if not files:
        raise FileNotFoundError(f"no .dcm files found under {args.path}")
    send_instances(
        files,
        host=args.host,
        port=args.port,
        calling_ae=args.calling_ae,
        called_ae=args.called_ae,
    )
    LOGGER.info("send_completed: %d instances", len(files))
