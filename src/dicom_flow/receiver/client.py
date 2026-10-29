from pathlib import Path

from pydicom import dcmread
from pynetdicom import AE

from dicom_flow.common.constants import ULTRASOUND_IMAGE_STORAGE, VERIFICATION


def send_instances(
    paths: list[Path],
    *,
    host: str,
    port: int,
    calling_ae: str = "SYNTHETIC_SCU",
    called_ae: str = "DICOMFLOW",
) -> None:
    ae = AE(ae_title=calling_ae)
    ae.add_requested_context(VERIFICATION)
    ae.add_requested_context(ULTRASOUND_IMAGE_STORAGE)

    association = ae.associate(host, port, ae_title=called_ae)
    if not association.is_established:
        raise ConnectionError(f"could not establish association with {host}:{port}")

    try:
        echo_status = association.send_c_echo()
        if echo_status is None or echo_status.Status != 0x0000:
            raise RuntimeError("C-ECHO failed")

        for path in paths:
            status = association.send_c_store(dcmread(path))
            if status is None or status.Status != 0x0000:
                raise RuntimeError(f"C-STORE failed for {path.name}")
    finally:
        association.release()


def collect_dicom_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("*.dcm"))
