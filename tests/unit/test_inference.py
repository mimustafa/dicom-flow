import json
from pathlib import Path

from dicom_flow.inference.config import load_config
from dicom_flow.inference.mock import infer_instance

CONFIG = Path(__file__).parents[2] / "src" / "dicom_flow" / "inference" / "mock_inference.yaml"


def test_config_hash_is_stable_and_tracks_file_content(tmp_path: Path) -> None:
    config = load_config(CONFIG)
    copied = tmp_path / "config.yaml"
    copied.write_bytes(CONFIG.read_bytes())
    assert load_config(copied).config_hash == config.config_hash

    copied.write_text(copied.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert load_config(copied).config_hash != config.config_hash


def test_mock_inference_is_deterministic() -> None:
    config = load_config(CONFIG)
    pixels = bytes(range(256)) * 16

    result_a = infer_instance(
        pixels,
        rows=64,
        columns=64,
        config=config,
        instance_seed=1,
    )
    result_b = infer_instance(
        pixels,
        rows=64,
        columns=64,
        config=config,
        instance_seed=1,
    )

    assert result_a == result_b
    assert result_a.classification == "demo-positive"


def test_mock_inference_matches_golden_output() -> None:
    config = load_config(CONFIG)
    actual = infer_instance(
        bytes(range(256)) * 16,
        rows=64,
        columns=64,
        config=config,
        instance_seed=1,
    )
    expected_path = Path(__file__).parents[1] / "fixtures" / "golden_inference.json"
    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    assert actual.model_dump(mode="json") == expected
