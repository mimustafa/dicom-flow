from pathlib import Path
from uuid import uuid4

from redis import Redis

from dicom_flow.common.config import ReceiverSettings
from dicom_flow.receiver.client import send_instances
from dicom_flow.receiver.server import create_receiver
from dicom_flow.synthetic import create_synthetic_study


def test_stored_instance_is_published_to_redis(
    tmp_path: Path,
    redis_client: Redis,
) -> None:
    stream = f"test:events:{uuid4().hex}"
    source = create_synthetic_study(tmp_path / "synthetic", instances=1)[0]
    receiver = create_receiver(
        ReceiverSettings(
            ae_title="DICOMFLOW",
            port=0,
            storage_dir=tmp_path / "received",
            allowed_calling_ae_titles="SYNTHETIC_SCU",
            event_stream=stream,
        ),
        host="127.0.0.1",
    )
    try:
        send_instances(
            [source],
            host="127.0.0.1",
            port=receiver.server_address[1],
        )
        entries = redis_client.xread({stream: "0-0"}, count=1)[0][1]
        assert len(entries) == 1
        _, fields = entries[0]
        assert fields["study_uid"]
        assert fields["series_uid"]
        assert fields["instance_uid"]
        assert fields["attempt"] == "0"
        assert len(list((tmp_path / "received").rglob("*.dcm"))) == 1
    finally:
        receiver.shutdown()
        receiver.server_close()
        redis_client.delete(stream)
