from typing import cast

from redis import Redis

from dicom_flow.worker.consumer import handle_failure


class RedisRecorder:
    def __init__(self) -> None:
        self.added: list[tuple[str, dict[str, str]]] = []
        self.acked: list[tuple[str, str, str]] = []

    def xadd(self, stream: str, fields: dict[str, str]) -> str:
        self.added.append((stream, fields))
        return "1-0"

    def xack(self, stream: str, group: str, message_id: str) -> int:
        self.acked.append((stream, group, message_id))
        return 1


def test_failed_message_retries_until_limit_then_dead_letters() -> None:
    redis_recorder = RedisRecorder()
    payload = {"study_uid": "1.2.3", "attempt": "0"}

    first_target = handle_failure(
        cast(Redis, redis_recorder),
        stream="dicom:instances",
        dead_letter_stream="dicom:dead-letter",
        group="workers",
        message_id="1-0",
        fields=payload,
        max_attempts=2,
    )
    second_target = handle_failure(
        cast(Redis, redis_recorder),
        stream="dicom:instances",
        dead_letter_stream="dicom:dead-letter",
        group="workers",
        message_id="2-0",
        fields={"study_uid": "1.2.3", "attempt": "1"},
        max_attempts=2,
    )

    assert first_target == "dicom:instances"
    assert second_target == "dicom:dead-letter"
    assert redis_recorder.added[0][1]["attempt"] == "1"
    assert redis_recorder.added[1][1]["attempt"] == "2"
    assert redis_recorder.added[1][1]["failure"] == "processing_failed"
    assert len(redis_recorder.acked) == 2
