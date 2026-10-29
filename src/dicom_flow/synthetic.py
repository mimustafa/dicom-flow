import random
from pathlib import Path

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from dicom_flow.common.constants import ULTRASOUND_IMAGE_STORAGE


def create_synthetic_study(
    output_dir: Path,
    *,
    instances: int = 2,
    seed: int = 1,
) -> list[Path]:
    if instances < 1:
        raise ValueError("instances must be at least 1")

    output_dir.mkdir(parents=True, exist_ok=True)
    study_uid = generate_uid()
    series_uid = generate_uid()
    rng = random.Random(seed)
    created: list[Path] = []

    for instance_number in range(1, instances + 1):
        sop_instance_uid = generate_uid()
        path = output_dir / f"{sop_instance_uid}.dcm"
        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = ULTRASOUND_IMAGE_STORAGE
        file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = generate_uid()

        dataset = FileDataset(
            str(path),
            {},
            file_meta=file_meta,
            preamble=b"\0" * 128,
        )
        dataset.SOPClassUID = ULTRASOUND_IMAGE_STORAGE
        dataset.SOPInstanceUID = sop_instance_uid
        dataset.PatientName = "SYNTHETIC^DEMO"
        dataset.PatientID = f"SYNTHETIC-{seed:04d}"
        dataset.PatientBirthDate = ""
        dataset.PatientSex = "O"
        dataset.StudyInstanceUID = study_uid
        dataset.SeriesInstanceUID = series_uid
        dataset.StudyID = "DEMO"
        dataset.StudyDate = "20260101"
        dataset.StudyTime = "120000"
        dataset.AccessionNumber = ""
        dataset.Modality = "US"
        dataset.SeriesNumber = 1
        dataset.InstanceNumber = instance_number
        dataset.Rows = 64
        dataset.Columns = 64
        dataset.SamplesPerPixel = 1
        dataset.PhotometricInterpretation = "MONOCHROME2"
        dataset.BitsAllocated = 8
        dataset.BitsStored = 8
        dataset.HighBit = 7
        dataset.PixelRepresentation = 0
        dataset.PixelData = bytes(rng.randrange(256) for _ in range(64 * 64))

        dataset.save_as(path, enforce_file_format=True)
        created.append(path)

    return created
