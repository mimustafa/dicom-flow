from pathlib import Path

import pytest
from pydicom import dcmread
from pydicom.dataset import Dataset

from dicom_flow.receiver.storage import InvalidDicomError, store_instance
from dicom_flow.synthetic import create_synthetic_study


def test_instance_uses_study_series_instance_layout(tmp_path: Path) -> None:
    source = create_synthetic_study(tmp_path / "input", instances=1)[0]
    dataset = dcmread(source)

    stored_path = store_instance(dataset, tmp_path / "received")

    assert stored_path.parent.parent.name == str(dataset.StudyInstanceUID)
    assert stored_path.parent.name == str(dataset.SeriesInstanceUID)
    assert stored_path.name == f"{dataset.SOPInstanceUID}.dcm"
    assert dcmread(stored_path).PixelData == dataset.PixelData


def test_storage_rejects_invalid_dataset(tmp_path: Path) -> None:
    with pytest.raises(InvalidDicomError, match="SOPClassUID"):
        store_instance(Dataset(), tmp_path)
