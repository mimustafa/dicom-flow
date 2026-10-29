import html
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from pydicom import dcmread

from dicom_flow.inference.config import InferenceConfig
from dicom_flow.inference.mock import InstanceInference, infer_instance

LOGGER = logging.getLogger(__name__)
DISCLAIMER = "Demo only. Not for clinical use."


def process_study(
    study_uid: str,
    *,
    storage_dir: Path,
    report_dir: Path,
    config: InferenceConfig,
) -> Path:
    study_dir = storage_dir / study_uid
    dicom_paths = sorted(study_dir.rglob("*.dcm"))
    if not dicom_paths:
        raise FileNotFoundError(f"no DICOM instances found for study {study_uid}")

    instances: list[dict[str, object]] = []
    for path in dicom_paths:
        dataset = dcmread(path)
        if str(dataset.StudyInstanceUID) != study_uid:
            raise ValueError(f"instance study UID does not match study directory: {path.name}")
        prediction: InstanceInference = infer_instance(
            dataset.PixelData,
            rows=int(dataset.Rows),
            columns=int(dataset.Columns),
            config=config,
            instance_seed=int(dataset.InstanceNumber),
        )
        instances.append(
            {
                "instance_uid": str(dataset.SOPInstanceUID),
                **prediction.model_dump(mode="json"),
            }
        )

    result: dict[str, object] = {
        "study_uid": study_uid,
        "model_version": config.model_version,
        "config_version": config.config_version,
        "config_hash": config.config_hash,
        "inference_timestamp": datetime.now(UTC).isoformat(),
        "disclaimer": DISCLAIMER,
        "instances": instances,
    }

    output_dir = report_dir / study_uid
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "result.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_html_report(result, output_dir / "report.html")
    LOGGER.info("study_processed")
    return json_path


def write_html_report(result: dict[str, object], path: Path) -> None:
    escaped_version = html.escape(str(result["model_version"]))
    escaped_hash = html.escape(str(result["config_hash"]))
    escaped_timestamp = html.escape(str(result["inference_timestamp"]))
    instance_rows = []
    instances = result["instances"]
    if isinstance(instances, list):
        for item in instances:
            if isinstance(item, dict):
                instance_rows.append(
                    "<li>"
                    + html.escape(str(item["instance_uid"]))
                    + ": "
                    + html.escape(str(item["classification"]))
                    + "</li>"
                )
    body = (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<title>dicom-flow demo report</title><body>"
        f"<h1>Study {html.escape(str(result['study_uid']))}</h1>"
        f"<p>Model version: {escaped_version}</p>"
        f"<p>Config hash: {escaped_hash}</p>"
        f"<p>Inference timestamp: {escaped_timestamp}</p>"
        f"<p><strong>{DISCLAIMER}</strong></p><ul>{''.join(instance_rows)}</ul>"
        "</body></html>"
    )
    path.write_text(body, encoding="utf-8")
