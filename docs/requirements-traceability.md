# Requirements traceability

Traceability for the demo implementation. It is not a regulatory submission.

| Requirement | Implementation | Verification |
|---|---|---|
| Generate synthetic ultrasound studies and fake pixels | `src/dicom_flow/synthetic.py` | `tests/unit/test_synthetic.py`; `synthetic_ultrasound_paths` fixture |
| Validate and persist DICOM instances by Study/Series/Instance UID | `src/dicom_flow/receiver/storage.py` | `tests/unit/test_storage.py`; `tests/integration/test_receiver.py` |
| Publish instance events after successful store | `src/dicom_flow/common/events.py`; `src/dicom_flow/receiver/server.py` | `tests/integration/test_redis_events.py` |
| Use Redis consumer groups, acknowledgement, bounded retries, and dead lettering | `src/dicom_flow/worker/consumer.py` | `tests/unit/test_retry.py`; `tests/e2e/test_pipeline.py` |
| Reproduce mock inference from a versioned config and recorded hash | `src/dicom_flow/inference/` | `tests/unit/test_inference.py`; `tests/fixtures/golden_inference.json` |
| Write a result and demo-disclaimed report per study | `src/dicom_flow/worker/processor.py` | `tests/e2e/test_pipeline.py` |
| Forward a result as DICOM Secondary Capture to allow-listed destination | `src/dicom_flow/forwarder/` | `tests/unit/test_forwarder_helpers.py`; `tests/integration/test_forwarder.py` |
| Keep trusted endpoint settings in environment and support outbound TLS | `src/dicom_flow/common/config.py`; `src/dicom_flow/forwarder/client.py` | `tests/unit/test_forwarder_helpers.py`; Compose configuration |
| Run quality checks, coverage threshold, and Docker build in CI | `.github/workflows/ci.yml`; `pyproject.toml` | CI job executes Ruff, mypy, pytest (70% threshold), and Docker build |
| Document known hazards and verification | `docs/risk-analysis.md`; `docs/verification-report-template.md` | Review with each demo release |
