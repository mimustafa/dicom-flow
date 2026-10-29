import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID, ExplicitVRLittleEndian

from dicom_flow.common.constants import SECONDARY_CAPTURE_IMAGE_STORAGE

PIXEL_SIDE = 64


def _stable_uid(value: str) -> UID:
    number = int.from_bytes(hashlib.sha256(value.encode("utf-8")).digest()[:16], "big")
    return UID(f"2.25.{number}")


def create_result_secondary_capture(result_path: Path) -> FileDataset:
    result: Any = json.loads(result_path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError("result JSON must contain an object")
    study_uid = result.get("study_uid")
    config_hash = result.get("config_hash")
    model_version = result.get("model_version")
    if not isinstance(study_uid, str) or not UID(study_uid).is_valid:
        raise ValueError("result contains an invalid study UID")
    if not isinstance(config_hash, str) or not isinstance(model_version, str):
        raise ValueError("result is missing inference provenance")

    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = SECONDARY_CAPTURE_IMAGE_STORAGE
    meta.MediaStorageSOPInstanceUID = _stable_uid(f"{study_uid}:{config_hash}:result")
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.ImplementationClassUID = _stable_uid("dicom-flow-demo")

    dataset = FileDataset(str(result_path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.set_original_encoding(False, True)
    dataset.SOPClassUID = SECONDARY_CAPTURE_IMAGE_STORAGE
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = UID(study_uid)
    dataset.SeriesInstanceUID = _stable_uid(f"{study_uid}:{config_hash}:series")
    dataset.Modality = "OT"
    dataset.ConversionType = "WSD"
    dataset.PatientName = "SYNTHETIC^DEMO"
    dataset.PatientID = "SYNTHETIC-DEMO"
    dataset.PatientSex = "O"
    now = datetime.now(UTC)
    dataset.StudyDate = now.strftime("%Y%m%d")
    dataset.StudyTime = now.strftime("%H%M%S.%f")
    dataset.SeriesNumber = 9001
    dataset.InstanceNumber = 1
    dataset.ImageType = ["DERIVED", "SECONDARY"]
    dataset.Rows = PIXEL_SIDE
    dataset.Columns = PIXEL_SIDE
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 8
    dataset.BitsStored = 8
    dataset.HighBit = 7
    dataset.PixelRepresentation = 0
    dataset.ImageComments = (
        f"Demo only. Not for clinical use. Model: {model_version}; config SHA-256: {config_hash}"
    )
    digest = hashlib.sha256(result_path.read_bytes()).digest()
    dataset.PixelData = (digest * ((PIXEL_SIDE * PIXEL_SIDE // len(digest)) + 1))[
        : PIXEL_SIDE * PIXEL_SIDE
    ]
    return dataset
