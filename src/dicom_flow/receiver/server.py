import logging
from pathlib import Path
from typing import Any

from pydicom.dataset import Dataset
from pynetdicom import AE, evt
from redis import RedisError

from dicom_flow.common.config import ReceiverSettings
from dicom_flow.common.constants import ULTRASOUND_IMAGE_STORAGE, VERIFICATION
from dicom_flow.common.events import EventPublisher, RedisStreamPublisher
from dicom_flow.receiver.storage import InvalidDicomError, store_instance

LOGGER = logging.getLogger(__name__)


def _store_handler(
    event: Any,
    *,
    storage_dir: Path,
    allowed_callers: frozenset[str],
    publisher: EventPublisher,
) -> int:
    if event.assoc.requestor.ae_title.strip().upper() not in allowed_callers:
        LOGGER.warning("store_rejected")
        return 0x0124

    try:
        dataset: Dataset = event.dataset
        dataset.file_meta = event.file_meta
        store_instance(dataset, storage_dir)
        publisher.publish_instance(dataset)
    except RedisError:
        LOGGER.error("store_event_publish_failed")
        return 0xA700
    except (InvalidDicomError, OSError, ValueError):
        LOGGER.warning("store_invalid_instance")
        return 0xC210

    LOGGER.info("store_completed")
    return 0x0000


def create_receiver(
    settings: ReceiverSettings,
    host: str = "0.0.0.0",
    publisher: EventPublisher | None = None,
) -> Any:
    ae = AE(ae_title=settings.ae_title)
    ae.require_calling_aet = list(settings.allowed_callers)
    ae.add_supported_context(VERIFICATION)
    ae.add_supported_context(ULTRASOUND_IMAGE_STORAGE)
    event_publisher = (
        publisher
        if publisher is not None
        else RedisStreamPublisher(settings.redis_url, settings.event_stream)
    )

    def store_handler(event: Any) -> int:
        return _store_handler(
            event,
            storage_dir=settings.storage_dir,
            allowed_callers=settings.allowed_callers,
            publisher=event_publisher,
        )

    return ae.start_server(
        (host, settings.port),
        block=False,
        evt_handlers=[(evt.EVT_C_STORE, store_handler)],
    )
