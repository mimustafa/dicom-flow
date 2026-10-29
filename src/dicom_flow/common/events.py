from typing import Protocol

from pydicom.dataset import Dataset
from redis import Redis


class EventPublisher(Protocol):
    def publish_instance(self, dataset: Dataset) -> None: ...


class RedisStreamPublisher:
    def __init__(self, redis_url: str, stream: str) -> None:
        self._redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self._stream = stream

    def publish_instance(self, dataset: Dataset) -> None:
        self._redis.xadd(
            self._stream,
            {
                "study_uid": str(dataset.StudyInstanceUID),
                "series_uid": str(dataset.SeriesInstanceUID),
                "instance_uid": str(dataset.SOPInstanceUID),
                "attempt": "0",
            },
        )
