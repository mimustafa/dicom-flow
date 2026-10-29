from collections.abc import Iterator

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
