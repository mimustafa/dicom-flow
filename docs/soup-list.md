# Software of unknown provenance (SOUP) list

Demo inventory. Direct dependency versions are constrained in `pyproject.toml`
and resolved exactly by `uv.lock`; transitive packages are also recorded in the
lockfile.

| Package | Locked version | Purpose |
|---|---:|---|
| pydicom | 3.0.2 | Read, validate, generate, and write DICOM datasets |
| pynetdicom | 3.0.4 | DICOM C-ECHO and C-STORE networking |
| pydantic | 2.14.1 | Typed configuration and inference schemas |
| pydantic-settings | 2.16.2 | Environment and `.env` configuration |
| redis | 6.4.0 | Redis Streams publishing and consumer groups |
| PyYAML | 6.0.3 | Safe loading of versioned inference YAML |
| pytest | 8.4.2 | Automated tests |
| pytest-cov | 7.1.0 | Test coverage measurement and threshold |
| Ruff | 0.17.3 | Linting and import checks |
| mypy | 1.20.2 | Strict static type checking |
| Redis | 7.4.12 (`redis@sha256:8da19c7399dca900c6822a1cf30f9d2285585e2c4b457ff4095b0f4500054d3f`) | Stream broker in Docker Compose |
| Orthanc | 1.13.0 (`orthancteam/orthanc@sha256:d2705f2c56547e55ce9bc2250fd22d05d326493b3f3d9fa191ecb7db8ca6b5a2`) | Demo DICOM destination in Docker Compose |
| Python | 3.12-slim image | Runtime container base |

These are demo dependency records, not a complete security assessment. Review
the lockfile and image tags before using the repository in a controlled
environment.
