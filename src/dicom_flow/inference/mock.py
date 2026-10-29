import random

from pydantic import BaseModel

from dicom_flow.inference.config import InferenceConfig


class Detection(BaseModel):
    label: str
    confidence: float
    box: tuple[int, int, int, int]


class InstanceInference(BaseModel):
    classification: str
    classification_score: float
    detections: list[Detection]


def infer_instance(
    pixel_data: bytes,
    *,
    rows: int,
    columns: int,
    config: InferenceConfig,
    instance_seed: int,
) -> InstanceInference:
    if not pixel_data or rows < 1 or columns < 1:
        raise ValueError("valid image pixels and dimensions are required")

    scale = config.preprocessing.scale
    mean_intensity = sum(pixel_data) / len(pixel_data) / scale
    score = min(1.0, max(0.0, mean_intensity))
    classification = (
        "demo-positive" if score >= config.classifier.positive_threshold else "demo-negative"
    )
    rng = random.Random(config.seed + instance_seed)
    confidence = min(1.0, max(0.0, score * rng.uniform(0.8, 1.0)))
    detections: list[Detection] = []
    if confidence >= config.detector.confidence_threshold:
        x1 = rng.randrange(columns)
        y1 = rng.randrange(rows)
        x2 = rng.randrange(x1 + 1, columns + 1)
        y2 = rng.randrange(y1 + 1, rows + 1)
        detections.append(
            Detection(
                label="mock-region",
                confidence=round(confidence, 6),
                box=(x1, y1, x2, y2),
            )
        )

    return InstanceInference(
        classification=classification,
        classification_score=round(score, 6),
        detections=detections,
    )
