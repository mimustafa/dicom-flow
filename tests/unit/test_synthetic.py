from pathlib import Path

import pytest
from pydicom import dcmread

from dicom_flow.synthetic import create_synthetic_study


def test_synthetic_study_contains_fake_ultrasound_instances(tmp_path: Path) -> None:
    paths = create_synthetic_study(tmp_path, instances=3, seed=7)

    assert len(paths) == 3
    datasets = [dcmread(path) for path in paths]
    assert {str(dataset.Modality) for dataset in datasets} == {"US"}
    assert {str(dataset.PatientName) for dataset in datasets} == {"SYNTHETIC^DEMO"}
    assert len({str(dataset.StudyInstanceUID) for dataset in datasets}) == 1
    assert len({str(dataset.SeriesInstanceUID) for dataset in datasets}) == 1
    assert len({str(dataset.SOPInstanceUID) for dataset in datasets}) == 3
    assert all(len(dataset.PixelData) == 64 * 64 for dataset in datasets)


def test_generator_rejects_empty_study(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        create_synthetic_study(tmp_path, instances=0)
