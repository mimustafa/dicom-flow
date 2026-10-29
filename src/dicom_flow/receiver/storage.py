from pathlib import Path

from pydicom.dataset import Dataset
from pydicom.uid import UID

from dicom_flow.common.constants import ULTRASOUND_IMAGE_STORAGE


class InvalidDicomError(ValueError):
    """Raised when an incoming object lacks required, safe-to-store DICOM data."""


def _validated_uid(dataset: Dataset, attribute: str) -> str:
    value = getattr(dataset, attribute, None)
    if not isinstance(value, str) or not UID(value).is_valid:
        raise InvalidDicomError(f"missing or invalid {attribute}")
    return value


def validate_instance(dataset: Dataset) -> None:
    required_uids = ("SOPClassUID", "SOPInstanceUID", "StudyInstanceUID", "SeriesInstanceUID")
    for attribute in required_uids:
        _validated_uid(dataset, attribute)

    if dataset.get("Modality") != "US" or dataset.get("SOPClassUID") != ULTRASOUND_IMAGE_STORAGE:
        raise InvalidDicomError("only ultrasound instances are accepted")
    if not isinstance(dataset.get("Rows"), int) or not isinstance(dataset.get("Columns"), int):
        raise InvalidDicomError("missing image dimensions")
    if dataset.Rows < 1 or dataset.Columns < 1:
        raise InvalidDicomError("image dimensions must be positive")
    if not isinstance(dataset.get("SamplesPerPixel"), int) or not isinstance(
        dataset.get("BitsAllocated"), int
    ):
        raise InvalidDicomError("missing pixel format")
    if dataset.SamplesPerPixel < 1 or dataset.BitsAllocated < 1:
        raise InvalidDicomError("pixel format must be positive")
    if not isinstance(dataset.get("PixelData"), bytes):
        raise InvalidDicomError("missing pixel data")

    bytes_per_sample = (dataset.BitsAllocated + 7) // 8
    expected_length = dataset.Rows * dataset.Columns * dataset.SamplesPerPixel * bytes_per_sample
    if len(dataset.PixelData) < expected_length:
        raise InvalidDicomError("pixel data is shorter than the declared image dimensions")


def store_instance(dataset: Dataset, storage_dir: Path) -> Path:
    validate_instance(dataset)
    study_uid = _validated_uid(dataset, "StudyInstanceUID")
    series_uid = _validated_uid(dataset, "SeriesInstanceUID")
    instance_uid = _validated_uid(dataset, "SOPInstanceUID")

    if not hasattr(dataset, "file_meta"):
        raise InvalidDicomError("missing file meta information")

    target_dir = storage_dir / study_uid / series_uid
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{instance_uid}.dcm"
    dataset.save_as(target_path, enforce_file_format=True)
    return target_path
