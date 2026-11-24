# Customer Feedback Intelligence System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 146 Passed](https://img.shields.io/badge/Tests-146%20Passed-brightgreen.svg)]()
[![Python: 3.10--3.12](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)]()

A smart, AI-driven customer feedback analysis platform designed to process raw feedback datasets, classify sentiments, topics, and urgency levels, compute business priority scores, deliver actionable insights through an interactive Streamlit dashboard, and provide an intelligent Generative AI assistant for customer feedback exploration.

---

## 🏗️ Architecture Overview

The system implements an end-to-end data processing and Generative AI analysis pipeline:

```text
Raw Feedback (CSV)
       │
       ▼
[Data Validation & Cleaning]  ──▶  src/preprocessing.py (Schema validation, anomaly removal)
       │
       ▼
[AI / Heuristic Classifier]   ──▶  src/classifier.py (Sentiment, Topic, Urgency)
       │
       ▼
[Priority Scoring Engine]     ──▶  src/priority.py (Weighted 0-100 score & PriorityLevel)
       │
       ▼
[Analytics & Insights]        ──▶  src/insights.py & src/executive_insights.py
       │
       ▼
[GenAI Feedback Assistant]   ──▶  src/ai_assistant.py (Grounded Q&A, citation validation)
       │
       ▼
[Interactive Dashboard]       ──▶  dashboard/app.py (Streamlit UI with Plotly charts & AI chat)
```

### Core Components
- **`src/preprocessing.py`**: Validates required columns, drops invalid/fractional ratings, removes duplicate IDs, handles whitespace/null values, and logs anomalies.
- **`src/classifier.py`**: Categorizes feedback into Sentiment (*Positive, Neutral, Negative*), Topic (*Pricing, Product Features, Customer Support, Billing, Performance, UI/UX, Other*), and Urgency (*Low, Medium, High, Critical*). Supports OpenAI structured LLM prompts and deterministic keyword/regex heuristic fallbacks.
- **`src/priority.py`**: Calculates a normalized 0–100 PriorityScore based on Customer Tier (Enterprise, Premium, Standard), Urgency, and Rating/Sentiment. Assigns PriorityLevels (*Critical, High, Medium, Low*) and human-readable PriorityReasons.
- **`src/insights.py`**: Computes overall KPIs, topic distributions, volume/negative trends over time, and customer segment risk profiles.
- **`src/executive_insights.py`**: Generates strategic executive briefings and recommendations using Pydantic schema validation and an in-memory bounded LRU/FIFO cache.
- **`src/ai_assistant.py`**: Genuine Generative AI assistant combining deterministic Pandas retrieval with OpenAI structured outputs, citation validation against retrieved records, prompt injection defense, and offline fallback.
- **`dashboard/app.py`**: Dark-themed multi-page Streamlit analytics application with interactive filters, trend charts, triage tables, sanitized CSV exports, and interactive AI Q&A panel.

---

## 🤖 Genuine GenAI Customer Feedback Assistant

The dashboard's **AI Insights** panel (`src/ai_assistant.py`) provides an intelligent assistant that answers analytical and investigative questions grounded strictly in customer feedback data:

### Key Capabilities
1. **Targeted Evidence Retrieval**: Uses Pandas filtering and keyword matching across topics, sentiments, customer tiers, and priority scores to retrieve relevant feedback records.
2. **Deterministic Numerical Calculation**: For questions involving metrics (average ratings, total counts, negative percentages), calculations are performed deterministically via Pandas to eliminate hallucinated statistics.
3. **Citation & Grounding Defense**: Extracts and validates feedback ID citations (e.g. `F001`, `F002`) against retrieved context. Hallucinated IDs not present in the evidence are automatically stripped.
4. **Actionable Suggestions**: Automatically extracts actionable product improvements and derived QA test scenarios.
5. **Prompt Injection Hardening**: Customer feedback text is encapsulated in `<feedback>` XML blocks with closing tags escaped, and system instructions forbid instruction execution from feedback content.
6. **Offline Deterministic Fallback**: When an OpenAI API key is unavailable or during API timeouts, the assistant seamlessly falls back to deterministic rule-grounded synthesis.

### Example Supported Questions
- *What are the major customer complaints?*
- *Why are customers dissatisfied?*
- *Summarise negative customer feedback.*
- *What are the critical customer issues?*
- *Which customer problems should management prioritise?*
- *Suggest test scenarios based on reported customer issues.*
- *Recommend improvements based on customer feedback.*
- *What are Enterprise customers saying about billing?*

---

## 📁 Project Structure

```text
customer-feedback-intelligence/
│
├── data/
│   ├── feedback.csv                   # Raw customer feedback dataset (327 records)
│   └── evaluation/
│       └── candidate_eval_set.json    # Candidate evaluation dataset (20 curated cases)
│
├── src/
│   ├── __init__.py                    # Source package initializer
│   ├── preprocessing.py               # Data loading, validation, and cleaning
│   ├── classifier.py                  # AI & heuristic classification
│   ├── priority.py                    # Priority scoring and guardrails
│   ├── insights.py                    # Analytical metrics and aggregations
│   ├── executive_insights.py          # Executive briefings and bounded cache
│   └── ai_assistant.py                # GenAI Feedback Assistant with citation validation
│
├── dashboard/
│   └── app.py                         # Streamlit analytics application with AI chat
│
├── output/
│   ├── cleaned_feedback.csv           # Cleaned dataset (321 records)
│   ├── classified_feedback.csv        # Classified dataset
│   ├── prioritized_feedback.csv       # Final prioritized dataset
│   └── priority_errors.log            # Validation error log
│
├── tests/
│   ├── conftest.py                    # Pytest shared fixtures
│   ├── test_ai_assistant.py           # GenAI Assistant unit & security tests (14 tests)
│   ├── test_genai_validation.py       # GenAI functional & guardrail tests (11 tests)
│   ├── test_unit_preprocessing.py     # Preprocessing unit tests (18 tests)
│   ├── test_unit_classifier.py        # Classifier unit tests (29 tests)
│   ├── test_unit_priority.py          # Priority scoring unit tests (20 tests)
│   ├── test_unit_insights.py          # Insights unit tests (16 tests)
│   ├── test_unit_executive_insights.py# Executive insights unit tests (12 tests)
│   ├── test_unit_main.py              # Main pipeline unit tests (4 tests)
│   ├── test_unit_dashboard.py         # Dashboard unit tests (7 tests)
│   ├── test_integration_pipeline.py   # End-to-end integration tests (6 tests)
│   ├── test_security.py               # Security vulnerability tests (5 tests)
│   ├── test_concurrency_failure.py    # Concurrency and negative tests (5 tests)
│   ├── test_performance.py            # Throughput & latency benchmarks (4 tests)
│   └── test_red_defects.py            # Red-Green-Refactor regression suite (6 tests)
│
├── BARN_DOOR_PROTOCOL_REPORT.md       # Comprehensive protocol audit & QA report
├── LICENSE                            # MIT License file
├── requirements.txt                   # Production dependencies
├── .env.example                       # Environment variable template
├── README.md                          # Project documentation
└── main.py                            # CLI pipeline entry point
```

---

## 🛠️ Setup & Installation

### 1. Prerequisites
- Python 3.10 to 3.12 installed on your machine.

### 2. Environment Setup

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt pytest pytest-mock
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt pytest pytest-mock
```

### 3. Environment Variables (Optional for Offline Mode)
```bash
cp .env.example .env
```
Provide your OpenAI API key in `.env` if utilizing live GPT classification and the AI Assistant:
```env
OPENAI_API_KEY=your_actual_api_key_here
OPENAI_MODEL=gpt-4o-mini
```
*(If no API key is provided, the system gracefully operates in deterministic offline fallback mode with zero runtime errors).*

---

## 🚀 Execution Instructions

### Run Complete End-to-End Pipeline (CLI)
```bash
python main.py
```
*Options:*
- `--priority-only`: Skip classification and recompute priority scores using existing `output/classified_feedback.csv`.
- `--force-classify`: Force re-classification of all records even if cached outputs exist.

### Launch Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```
Access the application at `http://localhost:8501`. Navigate to **AI Insights** in the sidebar to interact with the GenAI Customer Feedback Assistant.

---

## 🧪 Automated Testing

The project is covered by a **146-test automated suite** incorporating unit, integration, security, concurrency, performance, and GenAI assistant tests. All external OpenAI API interactions are mocked.

### Execute Full Test Suite
```bash
pytest -v
```

### Run GenAI Assistant Tests Specifically
```bash
pytest tests/test_ai_assistant.py -v
```

### Test Suite Breakdown
| Suite | Tests | Description |
|---|---|---|
| `tests/test_ai_assistant.py` | 14 | GenAI retrieval, stats, citation validation, prompt injection, fallback |
| `tests/test_genai_validation.py` | 11 | Behavioral Q&A, hallucination defense, prompt injection, telemetry |
| `tests/test_unit_preprocessing.py` | 18 | CSV loading, boundary checks, data quality |
| `tests/test_unit_classifier.py` | 29 | Heuristic & LLM sentiment/topic/urgency classification |
| `tests/test_unit_priority.py` | 20 | PriorityScore, tier weighting, guardrails |
| `tests/test_unit_insights.py` | 16 | Aggregations, monthly trends, segment risk |
| `tests/test_unit_executive_insights.py` | 12 | Executive briefing schemas, context hash, bounded cache |
| `tests/test_unit_main.py` | 4 | CLI pipeline execution & error handling |
| `tests/test_unit_dashboard.py` | 7 | Caching, badges, date handling, safe CSV export |
| `tests/test_integration_pipeline.py` | 6 | End-to-end multi-stage pipeline integration |
| `tests/test_security.py` | 5 | CSV formula injection, stored XSS, cache exhaustion, API key safety |
| `tests/test_concurrency_failure.py` | 5 | Thread safety, race condition simulation, unicode text |
| `tests/test_performance.py` | 4 | Preprocessing & scoring throughput benchmarks |
| `tests/test_red_defects.py` | 6 | Red-Green-Refactor verified defect regressions |
| **Total** | **157** | **100% Passing in ~1.4s** |

---

## 🔒 Security & Data Boundary Protection

1. **Prompt Injection Mitigation**: User query and customer feedback text are sanitized; XML delimiters (`<feedback>`, `<customer_feedback>`) are escaped (`[tag_escaped]`) to prevent instruction hijacking.
2. **Citation Provenance Validation**: The AI assistant validates every cited feedback ID against the actual retrieved context records, stripping hallucinated IDs.
3. **Deterministic Math Guard**: Numerical calculations are routed directly to Pandas to prevent fabricated statistics.
4. **CSV Formula Injection Mitigation (CWE-1236)**: `to_safe_csv_bytes()` prepends `'` to cells starting with `=`, `+`, `-`, `@`, `\t`, `\r`.
5. **Stored XSS Prevention (CWE-79)**: Dynamic fields in HTML blocks are sanitized via `html.escape()`.
6. **Bounded Caching (CWE-400)**: `_INSIGHTS_CACHE` uses `OrderedDict` with `MAX_CACHE_SIZE = 100` and FIFO eviction.
7. **Bounded Retries & Timeouts**: OpenAI client uses explicit `timeout=20.0` and `max_retries=2`.

---

## ⚠️ Known Limitations & Deployment Scope

### Current Status
**QUALIFIED PASS — CONTROLLED LOCAL SINGLE-USER USE ONLY**

### Documented Operational Boundaries
- **Approved For**: Local, single-analyst workstations running the CLI pipeline and local Streamlit dashboard (`localhost:8501`).
- **Shared Output-File Concurrency**: Shared filesystem outputs (`output/prioritized_feedback.csv`) lack write locks and remain unsafe for simultaneous multi-tenant write access.
- **Mocked vs. Live AI Testing**: Automated tests strictly use deterministic mocks to prevent API billing charges. A candidate evaluation dataset (`data/evaluation/candidate_eval_set.json`) is prepared with expected answers marked as `pending_human_review` for future live evaluation.
- **Physical Browser Verification**: Plotly visual rendering and click-to-download events were verified via code and data audits; live browser driver testing was blocked due to environment quota limits.

---

## 📄 License

This project is licensed under the **MIT License**. See the [`LICENSE`](LICENSE) file for complete terms and copyright details.

```text
Copyright (c) 2026 Anirudha Saxena
Licensed under the MIT License.
```
