from pathlib import Path
from uuid import uuid4

from redis import Redis

from dicom_flow.common.config import ReceiverSettings, WorkerSettings
from dicom_flow.common.events import RedisStreamPublisher
from dicom_flow.receiver.client import send_instances
from dicom_flow.receiver.server import create_receiver
from dicom_flow.synthetic import create_synthetic_study
from dicom_flow.worker.consumer import run_worker


def test_send_to_receiver_produces_study_report(
    tmp_path: Path,
    redis_client: Redis,
) -> None:
    stream = f"test:e2e:{uuid4().hex}"
    group = f"test-workers-{uuid4().hex}"
    source_files = create_synthetic_study(tmp_path / "synthetic", instances=2)
    receiver = create_receiver(
        ReceiverSettings(
            ae_title="DICOMFLOW",
            port=0,
            storage_dir=tmp_path / "received",
            allowed_calling_ae_titles="SYNTHETIC_SCU",
            event_stream=stream,
        ),
        host="127.0.0.1",
        publisher=RedisStreamPublisher("redis://localhost:6379/0", stream),
    )
    try:
        send_instances(
            source_files,
            host="127.0.0.1",
            port=receiver.server_address[1],
        )
    finally:
        receiver.shutdown()
        receiver.server_close()

    study_uid = next((tmp_path / "received").iterdir()).name
    settings = WorkerSettings(
        redis_url="redis://localhost:6379/0",
        event_stream=stream,
        dead_letter_stream=f"{stream}:dead",
        consumer_group=group,
        consumer_name="test-worker",
        storage_dir=tmp_path / "received",
        report_dir=tmp_path / "reports",
        block_ms=10,
    )
    run_worker(settings, stop_on_idle=True)

    result_path = tmp_path / "reports" / study_uid / "result.json"
    report_path = tmp_path / "reports" / study_uid / "report.html"
    assert result_path.is_file()
    assert report_path.is_file()
    result = result_path.read_text(encoding="utf-8")
    assert '"model_version": "mock-yolo-classifier-1.0"' in result
    assert '"config_hash":' in result
    assert "Demo only. Not for clinical use." in result
    assert "Demo only. Not for clinical use." in report_path.read_text(encoding="utf-8")
    redis_client.delete(stream, f"{stream}:dead")
