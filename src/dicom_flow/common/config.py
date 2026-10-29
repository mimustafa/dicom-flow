from pathlib import Path

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
    storage_dir: Path = Path("./data/received")
    report_dir: Path = Path("./data/reports")
    inference_config: Path = Path(__file__).parent.parent / "inference" / "mock_inference.yaml"
    max_attempts: int = 3
    block_ms: int = 1000
