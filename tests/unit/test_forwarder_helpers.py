import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from pydicom.uid import UID

from dicom_flow.common.config import ForwarderSettings
from dicom_flow.forwarder.dicom import create_result_secondary_capture


def test_result_is_converted_to_synthetic_secondary_capture(tmp_path: Path) -> None:
    study_uid = "1.2.826.0.1.3680043.8.498.123"
    result_path = tmp_path / "result.json"
    result_path.write_text(
        json.dumps(
            {
                "study_uid": study_uid,
                "config_hash": "a" * 64,
                "model_version": "mock-1",
                "instances": [],
            }
        ),
        encoding="utf-8",
    )

    dicom = create_result_secondary_capture(result_path)
    assert str(dicom.SOPClassUID) == "1.2.840.10008.5.1.4.1.1.7"
    assert dicom.StudyInstanceUID == UID(study_uid)
    assert dicom.PatientName == "SYNTHETIC^DEMO"
    assert len(dicom.PixelData) == 64 * 64
    assert "Not for clinical use" in dicom.ImageComments
    assert not result_path.with_name("result.dcm").exists()


def test_forwarder_rejects_destination_outside_both_allow_lists() -> None:
    settings = ForwarderSettings(
        destination_host="untrusted.example",
        destination_ae_title="UNKNOWN",
    )

    with pytest.raises(ValueError, match="host"):
        settings.validate_destination()

    settings.destination_host = "orthanc"
    with pytest.raises(ValueError, match="AE title"):
        settings.validate_destination()


def test_tls_client_key_requires_certificate() -> None:
    settings = ForwarderSettings(
        tls_enabled=True,
        tls_client_key=Path("client.key"),
        tls_client_cert=None,
    )

    with pytest.raises(ValueError, match="requires a TLS client certificate"):
        settings.validate_destination()


def test_empty_tls_environment_values_mean_tls_files_are_unset() -> None:
    with patch.dict(
        os.environ,
        {
            "DICOM_FLOW_TLS_CA_FILE": "",
            "DICOM_FLOW_TLS_CLIENT_CERT": "",
            "DICOM_FLOW_TLS_CLIENT_KEY": "",
        },
    ):
        settings = ForwarderSettings()

    assert settings.tls_ca_file is None
    assert settings.tls_client_cert is None
    assert settings.tls_client_key is None


def test_forwarder_specific_environment_names_are_loaded() -> None:
    with patch.dict(
        os.environ,
        {
            "DICOM_FLOW_FORWARD_STREAM": "results:to-forward",
            "DICOM_FLOW_FORWARD_MAX_ATTEMPTS": "5",
        },
    ):
        settings = ForwarderSettings()

    assert settings.forward_stream == "results:to-forward"
    assert settings.max_attempts == 5
