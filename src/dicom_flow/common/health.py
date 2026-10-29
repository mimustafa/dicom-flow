import socket

from redis import Redis

from dicom_flow.common.config import ForwarderSettings, ReceiverSettings, WorkerSettings


def _check_tcp(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=2):
        return


def _check_redis(redis_url: str) -> None:
    client: Redis = Redis.from_url(redis_url, socket_connect_timeout=2)
    try:
        client.ping()
    finally:
        client.close()


def check_health(service: str) -> None:
    if service == "receiver":
        _check_tcp("127.0.0.1", ReceiverSettings().port)
    elif service == "orthanc":
        _check_tcp("orthanc", 4242)
    elif service == "worker":
        _check_redis(WorkerSettings().redis_url)
    elif service == "forwarder":
        settings = ForwarderSettings()
        settings.validate_destination()
        _check_redis(settings.redis_url)
        _check_tcp(settings.destination_host, settings.destination_port)
    else:
        raise ValueError(f"unsupported health check: {service}")
