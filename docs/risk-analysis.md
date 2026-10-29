# Demo risk analysis

Lightweight, ISO 14971-inspired hazard identification for this educational
demo only. It is not a safety assessment and does not establish clinical
safety or regulatory compliance.

| Hazard | Possible cause | Potential effect | Demo controls / mitigation | Residual limitation |
|---|---|---|---|---|
| Real patient information is processed or logged | Operator sends non-synthetic DICOM | Unintended disclosure | README says synthetic data only; receiver logs omit DICOM attributes; generated identifiers are synthetic | The receiver cannot reliably determine whether arbitrary incoming DICOM is real |
| Incorrect inference is mistaken for clinical output | Mock result/report interpreted as diagnosis | Inappropriate clinical decision | Reports and forwarded SC carry “Demo only. Not for clinical use.”; classifier is explicitly mock | Disclaimers cannot prevent misuse |
| Untrusted DICOM sender reaches receiver | Unapproved calling AE title | Unwanted files or resource use | Calling AE-title allow-list; receiver only supports ultrasound image storage | AE titles are not cryptographic identity; network controls are still required |
| Result is forwarded to an unintended node | Destination configuration error | Data sent to wrong endpoint | Exact host and called-AE allow-lists; optional TLS certificate verification; Orthanc ports internal to Compose | Host allow-lists do not replace network segmentation or certificate management |
| Event or storage failure causes missing work | Redis or disk unavailable | Missing/stalled report or forwarding | Receiver returns failure on Redis publish error; worker and forwarder retry and dead-letter bounded failures | Pending message recovery and exactly-once delivery are not implemented |
| Duplicate report or forwarding | Per-instance events retrigger study processing | Duplicate remote objects or overwritten report | Stable study report path; deterministic SC instance UID | Duplicate network sends are possible; destination behavior varies |
| Secret exposure | Weak/local Orthanc password mishandled | Unauthorized access to Orthanc HTTP API | Password supplied via environment/local ignored `.env`; no committed runtime secret | Operators must provide and protect a strong secret |

