import logging
from collections.abc import Mapping
from typing import cast

from pydicom.errors import InvalidDicomError
from redis import Redis
from redis.exceptions import ResponseError

from dicom_flow.common.config import WorkerSettings
from dicom_flow.inference.config import InferenceConfig, load_config
from dicom_flow.worker.processor import process_study

LOGGER = logging.getLogger(__name__)


def ensure_consumer_group(redis_client: Redis, stream: str, group: str) -> None:
    try:
        redis_client.xgroup_create(stream, group, id="0", mkstream=True)
    except ResponseError as error:
        if "BUSYGROUP" not in str(error):
            raise


def handle_failure(
    redis_client: Redis,
    *,
    stream: str,
    dead_letter_stream: str,
    group: str,
    message_id: str,
    fields: Mapping[str, str],
    max_attempts: int,
) -> str:
    attempt = int(fields.get("attempt", "0")) + 1
    updated_fields: dict[
        str | int | float | bytes | bytearray | memoryview[int],
        str | int | float | bytes | bytearray | memoryview[int],
    ] = {key: value for key, value in fields.items()}
    updated_fields["attempt"] = str(attempt)
    target_stream = dead_letter_stream if attempt >= max_attempts else stream
    if target_stream == dead_letter_stream:
        updated_fields["failure"] = "processing_failed"
    redis_client.xadd(target_stream, updated_fields)
    redis_client.xack(stream, group, message_id)
    return target_stream


def process_message(
    redis_client: Redis,
    *,
    settings: WorkerSettings,
    config: InferenceConfig,
    message_id: str,
    fields: Mapping[str, str],
) -> None:
    try:
        study_uid = fields["study_uid"]
        process_study(
            study_uid,
            storage_dir=settings.storage_dir,
            report_dir=settings.report_dir,
            config=config,
        )
    except (InvalidDicomError, KeyError, OSError, ValueError) as error:
        target_stream = handle_failure(
            redis_client,
            stream=settings.event_stream,
            dead_letter_stream=settings.dead_letter_stream,
            group=settings.consumer_group,
            message_id=message_id,
            fields=fields,
            max_attempts=settings.max_attempts,
        )
        LOGGER.warning(
            "study_processing_failed (%s)",
            type(error).__name__,
            extra={"retry_stream": target_stream},
        )
        return

    redis_client.xadd(
        settings.forward_stream,
        {"study_uid": study_uid, "attempt": "0"},
    )
    redis_client.xack(settings.event_stream, settings.consumer_group, message_id)


def run_worker(settings: WorkerSettings, *, stop_on_idle: bool = False) -> None:
    if settings.max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
    ensure_consumer_group(redis_client, settings.event_stream, settings.consumer_group)
    config = load_config(settings.inference_config)
    LOGGER.info("worker_started")

    while True:
        entries = cast(
            list[tuple[str, list[tuple[str, dict[str, str]]]]],
            redis_client.xreadgroup(
                settings.consumer_group,
                settings.consumer_name,
                {settings.event_stream: ">"},
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
                process_message(
                    redis_client,
                    settings=settings,
                    config=config,
                    message_id=message_id,
                    fields=fields,
                )
