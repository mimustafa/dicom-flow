import json
from pathlib import Path
from uuid import uuid4

from dicom_flow.forwarder.service import run_forwarder
from pydicom.dataset import Dataset
from pynetdicom import AE, evt
from pynetdicom.sop_class import SecondaryCaptureImageStorage
from redis import Redis

from dicom_flow.common.config import ForwarderSettings


def test_forwarder_sends_secondary_capture_to_allowlisted_scp(
    tmp_path: Path,
    redis_client: Redis,
) -> None:
    received: list[str] = []
    scp = AE(ae_title="TESTDEST")
    scp.add_supported_context(SecondaryCaptureImageStorage)

    def store(event: evt.Event) -> int:
        dataset: Dataset = event.dataset
        received.append(str(dataset.SOPClassUID))
        return 0x0000

    server = scp.start_server(
        ("127.0.0.1", 0),
        block=False,
        evt_handlers=[(evt.EVT_C_STORE, store)],
    )
    stream = f"test:forward:{uuid4().hex}"
    group = f"test-forwarders-{uuid4().hex}"
    result_dir = tmp_path / "reports" / "1.2.3"
    result_dir.mkdir(parents=True)
    (result_dir / "result.json").write_text(
        json.dumps(
            {
                "study_uid": "1.2.3",
                "config_hash": "b" * 64,
                "model_version": "mock-1",
                "instances": [],
            }
        ),
        encoding="utf-8",
    )
    redis_client.xadd(stream, {"study_uid": "1.2.3", "attempt": "0"})
    settings = ForwarderSettings(
        redis_url="redis://localhost:6379/0",
        forward_stream=stream,
        dead_letter_stream=f"{stream}:dead",
        consumer_group=group,
        consumer_name="test-forwarder",
        report_dir=tmp_path / "reports",
        destination_host="127.0.0.1",
        destination_port=server.server_address[1],
        destination_ae_title="TESTDEST",
        trusted_destination_hosts="127.0.0.1",
        trusted_destination_ae_titles="TESTDEST",
        block_ms=10,
    )
    try:
        run_forwarder(settings, stop_on_idle=True)
        assert received == ["1.2.840.10008.5.1.4.1.1.7"]
        assert redis_client.xpending(stream, group)["pending"] == 0
    finally:
        server.shutdown()
        server.server_close()
        redis_client.xgroup_destroy(stream, group)
        redis_client.delete(stream, f"{stream}:dead")
