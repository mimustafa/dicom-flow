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

    @property
    def allowed_callers(self) -> frozenset[str]:
        return frozenset(
            title.strip().upper()
            for title in self.allowed_calling_ae_titles.split(",")
            if title.strip()
        )
