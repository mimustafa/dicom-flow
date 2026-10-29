from pathlib import Path

from pydicom import dcmread
from pydicom.dataset import Dataset
from pynetdicom import AE

from dicom_flow.common.config import ReceiverSettings
from dicom_flow.common.constants import ULTRASOUND_IMAGE_STORAGE, VERIFICATION
from dicom_flow.receiver.server import create_receiver


class RecordingPublisher:
    def __init__(self) -> None:
        self.instance_uids: list[str] = []

    def publish_instance(self, dataset: Dataset) -> None:
        self.instance_uids.append(str(dataset.SOPInstanceUID))


def test_synthetic_study_is_stored_by_network_receiver(
    tmp_path: Path,
    synthetic_ultrasound_paths: list[Path],
) -> None:
    source_files = synthetic_ultrasound_paths
    publisher = RecordingPublisher()
    receiver = create_receiver(
        ReceiverSettings(
            ae_title="DICOMFLOW",
            port=0,
            storage_dir=tmp_path / "received",
            allowed_calling_ae_titles="SYNTHETIC_SCU",
        ),
        host="127.0.0.1",
        publisher=publisher,
    )
    port = receiver.server_address[1]
    try:
        sender = AE(ae_title="SYNTHETIC_SCU")
        sender.add_requested_context(VERIFICATION)
        sender.add_requested_context(ULTRASOUND_IMAGE_STORAGE)
        association = sender.associate("127.0.0.1", port, ae_title="DICOMFLOW")
        assert association.is_established

        try:
            assert association.send_c_echo().Status == 0x0000
            for source in source_files:
                assert association.send_c_store(dcmread(source)).Status == 0x0000
        finally:
            association.release()

        stored_files = list((tmp_path / "received").rglob("*.dcm"))
        assert len(stored_files) == 2
        assert len(publisher.instance_uids) == 2
        for source in source_files:
            original = dcmread(source)
            stored = tmp_path / "received" / str(original.StudyInstanceUID)
            stored = stored / str(original.SeriesInstanceUID) / f"{original.SOPInstanceUID}.dcm"
            assert stored.is_file()
            assert dcmread(stored).SOPInstanceUID == original.SOPInstanceUID
    finally:
        receiver.shutdown()
        receiver.server_close()


def test_receiver_rejects_unlisted_calling_ae(tmp_path: Path) -> None:
    receiver = create_receiver(
        ReceiverSettings(
            port=0,
            storage_dir=tmp_path / "received",
            allowed_calling_ae_titles="SYNTHETIC_SCU",
        ),
        host="127.0.0.1",
    )
    try:
        sender = AE(ae_title="UNTRUSTED_SCU")
        sender.add_requested_context(VERIFICATION)
        association = sender.associate(
            "127.0.0.1",
            receiver.server_address[1],
            ae_title="DICOMFLOW",
        )
        assert not association.is_established
    finally:
        receiver.shutdown()
        receiver.server_close()
