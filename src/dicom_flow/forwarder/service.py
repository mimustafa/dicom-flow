import logging
from collections.abc import Mapping
from typing import cast

from pydicom.errors import InvalidDicomError
from redis import Redis
from redis.exceptions import ResponseError

from dicom_flow.common.config import ForwarderSettings
from dicom_flow.forwarder.client import send_result
from dicom_flow.worker.consumer import handle_failure

LOGGER = logging.getLogger(__name__)


def _ensure_group(client: Redis, settings: ForwarderSettings) -> None:
    try:
        client.xgroup_create(
            settings.forward_stream,
            settings.consumer_group,
            id="0",
            mkstream=True,
        )
    except ResponseError as error:
        if "BUSYGROUP" not in str(error):
            raise


def _forward_message(
    client: Redis,
    settings: ForwarderSettings,
    message_id: str,
    fields: Mapping[str, str],
) -> None:
    try:
        study_uid = fields["study_uid"]
        result_path = settings.report_dir / study_uid / "result.json"
        send_result(result_path, settings)
    except (
        ConnectionError,
        InvalidDicomError,
        KeyError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        handle_failure(
            client,
            stream=settings.forward_stream,
            dead_letter_stream=settings.dead_letter_stream,
            group=settings.consumer_group,
            message_id=message_id,
            fields=fields,
            max_attempts=settings.max_attempts,
        )
        LOGGER.warning("result_forward_failed (%s)", type(error).__name__)
        return
    client.xack(settings.forward_stream, settings.consumer_group, message_id)
    LOGGER.info("result_forwarded")


def run_forwarder(settings: ForwarderSettings, *, stop_on_idle: bool = False) -> None:
    settings.validate_destination()
    if settings.max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
    _ensure_group(client, settings)
    LOGGER.info("forwarder_started")
    while True:
        entries = cast(
            list[tuple[str, list[tuple[str, dict[str, str]]]]],
            client.xreadgroup(
                settings.consumer_group,
                settings.consumer_name,
                {settings.forward_stream: ">"},
                count=1,
                block=settings.block_ms,
            ),
        )
        if not entries:
            if stop_on_idle:
                return
            continue
        for _, messages in entries:
            for message_id, fields in messages:
                _forward_message(client, settings, message_id, fields)
