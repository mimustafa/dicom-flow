import ssl
from pathlib import Path

from pynetdicom import AE

from dicom_flow.common.config import ForwarderSettings
from dicom_flow.common.constants import SECONDARY_CAPTURE_IMAGE_STORAGE
from dicom_flow.forwarder.dicom import create_result_secondary_capture


def send_result(result_path: Path, settings: ForwarderSettings) -> None:
    settings.validate_destination()
    dataset = create_result_secondary_capture(result_path)

    tls_args: tuple[ssl.SSLContext, str] | None = None
    if settings.tls_enabled:
        context = ssl.create_default_context(cafile=settings.tls_ca_file)
        if settings.tls_client_cert is not None:
            context.load_cert_chain(
                certfile=settings.tls_client_cert,
                keyfile=settings.tls_client_key,
            )
        tls_args = (context, settings.destination_host)

    ae = AE(ae_title=settings.calling_ae_title)
    ae.add_requested_context(SECONDARY_CAPTURE_IMAGE_STORAGE)
    association = ae.associate(
        settings.destination_host,
        settings.destination_port,
        ae_title=settings.destination_ae_title,
        tls_args=tls_args,
    )
    if not association.is_established:
        raise ConnectionError("could not establish DICOM association with trusted destination")
    try:
        status = association.send_c_store(dataset)
        if status is None or status.Status != 0x0000:
            raise RuntimeError("destination returned an unsuccessful C-STORE status")
    finally:
        association.release()
