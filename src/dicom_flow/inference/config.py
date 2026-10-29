import hashlib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ConfigDict, Field


class PreprocessingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scale: float = Field(gt=0)


class DetectorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confidence_threshold: float = Field(ge=0, le=1)


class ClassifierConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    positive_threshold: float = Field(ge=0, le=1)


class InferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    config_version: str
    model_version: str
    seed: int
    preprocessing: PreprocessingConfig
    detector: DetectorConfig
    classifier: ClassifierConfig
    config_hash: str


def load_config(path: Path) -> InferenceConfig:
    raw = path.read_bytes()
    parsed: Any = yaml.safe_load(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"inference config must be a YAML mapping: {path}")
    config_hash = hashlib.sha256(raw).hexdigest()
    return InferenceConfig.model_validate({**parsed, "config_hash": config_hash})
