from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ReceiverSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DICOM_FLOW_",
        env_file=".env",
        extra="ignore",
    )

    ae_title: str = "DICOMFLOW"
    port: int = 11112
    storage_dir: Path = Path("./data/received")
    allowed_calling_ae_titles: str = "SYNTHETIC_SCU"
    redis_url: str = "redis://localhost:6379/0"
    event_stream: str = "dicom:instances"

    @property
    def allowed_callers(self) -> frozenset[str]:
        return frozenset(
            title.strip().upper()
            for title in self.allowed_calling_ae_titles.split(",")
            if title.strip()
        )


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DICOM_FLOW_",
        env_file=".env",
        extra="ignore",
    )

    redis_url: str = "redis://localhost:6379/0"
    event_stream: str = "dicom:instances"
    dead_letter_stream: str = "dicom:dead-letter"
    consumer_group: str = "dicom-workers"
    consumer_name: str = "worker-1"
    forward_stream: str = "dicom:forward"
    storage_dir: Path = Path("./data/received")
    report_dir: Path = Path("./data/reports")
    inference_config: Path = Path(__file__).parent.parent / "inference" / "mock_inference.yaml"
    max_attempts: int = 3
    block_ms: int = 1000


class ForwarderSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DICOM_FLOW_",
        env_file=".env",
        extra="ignore",
        populate_by_name=True,
        env_ignore_empty=True,
    )

    redis_url: str = "redis://localhost:6379/0"
    forward_stream: str = Field(
        default="dicom:forward",
        validation_alias="DICOM_FLOW_FORWARD_STREAM",
    )
    dead_letter_stream: str = Field(
        default="dicom:forward-dead-letter",
        validation_alias="DICOM_FLOW_FORWARD_DEAD_LETTER_STREAM",
    )
    consumer_group: str = Field(
        default="dicom-forwarders",
        validation_alias="DICOM_FLOW_FORWARD_CONSUMER_GROUP",
    )
    consumer_name: str = Field(
        default="forwarder-1",
        validation_alias="DICOM_FLOW_FORWARD_CONSUMER_NAME",
    )
    report_dir: Path = Path("./data/reports")
    destination_host: str = "orthanc"
    destination_port: int = 4242
    destination_ae_title: str = "ORTHANC"
    calling_ae_title: str = "DICOMFLOW"
    trusted_destination_hosts: str = "orthanc"
    trusted_destination_ae_titles: str = "ORTHANC"
    max_attempts: int = Field(default=3, validation_alias="DICOM_FLOW_FORWARD_MAX_ATTEMPTS")
    block_ms: int = 1000
    tls_enabled: bool = False
    tls_ca_file: Path | None = None
    tls_client_cert: Path | None = None
    tls_client_key: Path | None = None

    @property
    def trusted_hosts(self) -> frozenset[str]:
        return frozenset(
            host.strip().lower()
            for host in self.trusted_destination_hosts.split(",")
            if host.strip()
        )

    @property
    def trusted_ae_titles(self) -> frozenset[str]:
        return frozenset(
            title.strip().upper()
            for title in self.trusted_destination_ae_titles.split(",")
            if title.strip()
        )

    def validate_destination(self) -> None:
        if self.destination_host.strip().lower() not in self.trusted_hosts:
            raise ValueError("destination host is not in the trusted host allow-list")
        if self.destination_ae_title.strip().upper() not in self.trusted_ae_titles:
            raise ValueError("destination AE title is not in the trusted AE allow-list")
        if not 1 <= self.destination_port <= 65535:
            raise ValueError("destination port must be between 1 and 65535")
        if self.tls_enabled and self.tls_client_key and not self.tls_client_cert:
            raise ValueError("TLS client key requires a TLS client certificate")
