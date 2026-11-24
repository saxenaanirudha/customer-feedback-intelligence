# Changelog

All notable changes to the Customer Feedback Intelligence System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] - 2026-11-24

### Added
- **Genuine Generative AI Feedback Assistant** (`src/ai_assistant.py`):
  - Intelligent natural language question answering grounded strictly in customer feedback records.
  - Targeted evidence retrieval combining keyword matching across topics, sentiments, customer tiers, and priority scores.
  - Deterministic Pandas calculations for numerical inquiries (e.g. counts, averages, rating metrics) to eliminate hallucinated statistics.
  - Automated citation provenance validation stripping any non-existent feedback IDs from model outputs.
  - Actionable product improvement recommendations and QA test scenario generation derived directly from customer bug reports.
  - Prompt injection mitigation encapsulating customer feedback in `<feedback>` XML blocks with escaped closing tags.
  - Resilient offline fallback engine providing data-grounded synthesis when OpenAI API keys are unavailable or when API errors occur.
- **Candidate Evaluation Dataset** (`data/evaluation/candidate_eval_set.json`):
  - 20 curated evaluation queries covering synthesis, root cause analysis, summarization, critical priority triage, management recommendations, QA test scenarios, customer tier slices, out-of-domain abstention, adversarial prompt injection, and deterministic numerical calculations.
- **Automated GenAI Test Suites**:
  - `tests/test_ai_assistant.py` (14 unit, security, and fallback tests).
  - `tests/test_genai_validation.py` (11 functional, citation validation, hallucination defense, prompt injection, and API resilience tests).
- **Interactive AI Insights Dashboard Integration** (`dashboard/app.py`):
  - In-page interactive query input bar in the AI Insights panel.
  - Live AI vs. Deterministic Fallback engine status badges with request latency telemetry.
  - Visual supporting citation badges with active feedback ID links.
- **Comprehensive GenAI Validation Report** (`GENAI_TESTING_REPORT.md`).
- **Barn Door Protocol v3.0 QA Report** (`BARN_DOOR_PROTOCOL_V3_REPORT.md`).

### Fixed
- **GENAI-01**: Resolved issue where an empty LLM response string (`content=""`) parsed as `{}` and returned `"No answer generated."` without triggering offline fallback. Added explicit content validation raising `ValueError` and routing to fallback.

### Security
- Delimiter neutralization escaping `</feedback>` and `</customer_feedback>` tags in user queries and retrieved feedback items.
- Strict citation validation preventing model citation fabrication.

---

## [2.0.0] - 2026-11-24

### Added
- **Barn Door Protocol Audit & Remediation**:
  - Full Red → Green → Refactor regression suite (`tests/test_red_defects.py`).
  - 132 automated tests across unit, integration, security, concurrency, and performance categories.
  - MIT License root file and README documentation.

### Fixed
- **DEF-01**: Fixed `AttributeError` when `error_log_path=None` in `src/priority.py`.
- **DEF-02**: Fixed float rating parsing (`2.0` scoring 67 instead of 70).
- **DEF-03**: Resolved critical PriorityLevel label mismatch between `src/insights.py` and `dashboard/app.py`, correcting the High/Critical dashboard KPI from 0 to 122.
- **DEF-04**: Handled empty-dataset execution in `main.py` without `ValueError`.
- **DEF-05**: Fixed keyword collision in `src/classifier.py` where `"rep"` in customer support matched `"reports"`.

### Security
- **SEC-01**: Centralized CSV formula injection mitigation (`to_safe_csv_bytes()`).
- **SEC-02**: LLM prompt injection boundary enforcement in classifier.
- **SEC-03**: Stored XSS prevention via `html.escape()`.
- **SEC-04**: Bounded `_INSIGHTS_CACHE` memory growth with FIFO eviction (`MAX_CACHE_SIZE = 100`).
- **SEC-05**: Explicit network timeouts (`timeout=20.0`) and bounded retries (`max_retries=2`).

---

## [1.0.0] - 2026-08-30

### Added
- Initial pipeline implementation: Preprocessing, LLM/heuristic classification, priority scoring, analytics, and Streamlit dashboard.
