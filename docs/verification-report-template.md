# Verification report template

> Demo verification record only. Not a regulatory verification report.

## Run information

- Build/version:
- Git revision:
- Date:
- Operator:
- Python / uv:
- Docker / Compose:

## Scope and environment

- Requirements covered:
- Environment and service configuration:
- Confirmation that only generated synthetic DICOM was used:

## Results

| Check | Command / procedure | Expected result | Actual result | Pass / fail |
|---|---|---|---|---|
| Unit, integration, and e2e tests | `uv run pytest` | Tests pass; coverage at or above configured threshold | | |
| Ruff | `uv run ruff check .` | No findings | | |
| Mypy | `uv run mypy` | No type errors | | |
| Compose configuration | `docker compose config --quiet` | Valid configuration | | |
| Container build | `docker compose build` | All service images build | | |
| Synthetic pipeline | Generate -> send -> report -> forward | Synthetic result/report and destination object verified | | |

## Deviations, anomalies, and disposition

-

## Approval

- Reviewed by:
- Date:
- Decision:
