from collections.abc import Iterator
from pathlib import Path

import pytest
from redis import Redis
from redis.exceptions import RedisError


@pytest.fixture
def redis_client() -> Iterator[Redis]:
    client: Redis = Redis.from_url(
        "redis://localhost:6379/0",
        decode_responses=True,
        socket_connect_timeout=1,
    )
    try:
        client.ping()
    except RedisError:
        pytest.skip("Redis integration tests require docker compose up")
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def synthetic_ultrasound_paths(tmp_path: Path) -> list[Path]:
    from dicom_flow.synthetic import create_synthetic_study

    return create_synthetic_study(tmp_path / "synthetic-fixture", instances=2, seed=41)
