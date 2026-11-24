# LinkedIn Portfolio Screenshot & Carousel Guide
## Customer Feedback Intelligence System (v3.0.0 — GenAI Edition)

**Project:** Customer Feedback Intelligence Platform with GenAI Assistant & AI Quality Engineering  
**Version:** `v3.0.0`  
**Target Audience:** Senior AI Engineers, Quality Engineering Leaders, Tech Hiring Managers & System Architects  
**Resolution Standard:** High-Resolution 1920 × 993 (Widescreen presentation layout)  
**Theme:** Premium Dark SaaS Theme (`#070A13` / `#0A0E1A` with `#38BDF8` slate cyan accents)  
**Release Scope:** Qualified Pass for Controlled Local Single-User Use Only

---

## ⚠️ Important UI / Version Notice

> [!NOTE]
> **Sidebar Cosmetic Version Label:** The Streamlit dashboard sidebar displays a cosmetic label:
> `Feedback IQ v1.0.0 • © 2026 All rights reserved` (defined in `dashboard/app.py`).
> In strict compliance with project release constraints, application source code was frozen and preserved without modification. The underlying platform, test baseline (157 tests), data models, and documentation reflect **v3.0.0**.

---

## 1. Recommended LinkedIn Carousel Sequence & Post Captions

### Slide 1: Main Analytics Dashboard
* **File:** [`01_main_analytics_dashboard.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/01_main_analytics_dashboard.png)
* **Title:** Executive Overview & Live KPI Metrics
* **Carousel Headline:** *Customer Feedback Intelligence: Real-Time Analytics & Risk Triage*
* **Recommended Caption:**
  > "How do you transform 300+ unstructured customer feedback records into prioritized engineering action in milliseconds? Feedback IQ: a complete intelligence platform combining real-time sentiment distribution, customer tier segmentation, and interactive KPI sparklines."

---

### Slide 2: Classification & Issue Prioritization
* **File:** [`02_feedback_classification_prioritization.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/02_feedback_classification_prioritization.png)
* **Title:** Multi-Dimensional Priority Scoring Matrix
* **Carousel Headline:** *Automated Topic Classification & Mathematically Bounded Priority Scoring*
* **Recommended Caption:**
  > "Not all customer issues are created equal. Feedback IQ pairs deterministic topic classification with a mathematically bounded PriorityScore formula [18–100], weighting enterprise customer tiers (+15), urgency signals (+30), and sentiment to surface the top 122 High/Critical blockers instantly."

---

### Slide 3: Strategic Executive Briefing
* **File:** [`03_executive_insights_recommendations.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/03_executive_insights_recommendations.png)
* **Title:** Actionable Executive Insights & Risk Roadmap
* **Carousel Headline:** *From Bug Reports to Business Impact: Strategic Executive Insights*
* **Recommended Caption:**
  > "Bridging engineering triage with operational strategy. Feedback IQ synthesizes high-priority patterns into categorized business risks (Billing, UI/UX, Performance) and prioritizes actionable remediation roadmaps with bounded FIFO caching."

---

### Slide 4: GenAI Feedback Assistant
* **File:** [`04_genai_feedback_assistant_query.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/04_genai_feedback_assistant_query.png)
* **Title:** Data-Grounded Natural Language Question Answering
* **Carousel Headline:** *Grounded Natural Language Q&A with Provenance Citation Tracking*
* **Actual Question Asked:** *"What are the major customer complaints regarding billing?"*
* **Actual Rendered Response:**
  - *Answer:* Identifies negative sentiment concentration in Billing, Pricing, and Performance (124 negative out of 321 records, 122 High/Critical).
  - *Feedback Citations:* `F326`, `F205`, `F240`, `F096`, `F086` (from 12 retrieved records).
  - *Recommended Improvements:* Address root causes in Billing; accelerate SLA response times for critical enterprise tickets.
  - *Suggested QA Test Scenarios:* Regression test Billing flows under high concurrency; verify automated error notifications for failed customer workflows.
  - *Engine Status:* `Engine: Deterministic Fallback • Latency: 3ms`.
* **Recommended Caption:**
  > "Asking complex questions directly against feedback evidence. The AI Assistant retrieves targeted feedback records, validates citations against real feedback IDs, and provides actionable recommendations with transparent latency telemetry and offline fallback."

---

### Slide 5: Deterministic Numerical Accuracy
* **File:** [`05_deterministic_numerical_accuracy.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/05_deterministic_numerical_accuracy.png)
* **Title:** Mathematical Calculation Routing via Pandas
* **Carousel Headline:** *Guaranteed Mathematical Accuracy: Routing Numerical Math Directly to DataFrames*
* **Actual Question Asked:** *"How many critical priority issues are recorded?"*
* **Actual Rendered Response:**
  - *Answer:* *"In total, there are 122 combined High and Critical priority issues: 16 Critical Priority and 106 High Priority issues out of 321 total feedback records."*
  - *Ground Truth Match:* Exactly 16 Critical, 106 High, 122 Combined, 321 Total.
  - *Feedback Citations:* `F326`, `F274`, `F206`, `F205`, `F144`.
  - *Engine Status:* `Engine: Deterministic Fallback • Latency: 4ms`.
* **Recommended Caption:**
  > "LLMs frequently hallucinate counts and averages. In Feedback IQ, numerical queries are routed directly to Pandas calculations. Asking 'How many critical priority issues are recorded?' returns the mathematically exact ground truth: 16 Critical, 106 High, and 122 combined out of 321 records in 4ms."

---

### Slide 6: AI-Assisted QA Scenario Generation
* **File:** [`06_qa_test_scenario_generation.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/06_qa_test_scenario_generation.png)
* **Title:** Automated QA Test Scenarios & Graceful Fallback
* **Carousel Headline:** *Closing the Feedback Loop: Generating Targeted Test Cases from Customer Pain Points*
* **Actual Question Asked:** *"Generate QA test scenarios based on customer complaints related to billing and performance."*
* **Actual Rendered Response:**
  - *Targeted QA Scenarios:* Concurrency regression tests for Billing; automated error notification verification on failed customer workflows.
  - *Feedback Citations:* `F326`, `F274`, `F101`, `F086`, `F144`.
  - *Engine Status:* `Engine: Deterministic Fallback • Latency: 4ms`.
* **Recommended Caption:**
  > "Turning real customer bug reports into QA test suites. Feedback IQ extracts customer pain points into targeted test scenarios. Transparent badges clearly label engine status (Live AI vs. Deterministic Fallback)."

---

### Slide 7: Automated Test Suite Execution Evidence
* **File:** [`07_automated_pytest_results.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/07_automated_pytest_results.png)
* **Title:** Raw Pytest Terminal Execution Baseline
* **Carousel Headline:** *Quality Engineering at the Core: 157 Passing Automated Tests in 1.7s*
* **Execution Evidence:** Raw terminal execution of `pytest -v` across all 14 test modules (with sensitive local paths sanitized to `./customer-feedback-intelligence`).
* **Recommended Caption:**
  > "Real software engineering requires comprehensive automated verification. Feedback IQ is backed by 157 automated tests across 14 modules: unit tests, pipeline integrations, concurrency race-condition simulations, throughput benchmarks (>1,000 rec/s), and Red-Green-Refactor defect remediations."

---

### Slide 8: Barn Door Protocol QA Audit
* **File:** [`08_barn_door_protocol_qa_report.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/08_barn_door_protocol_qa_report.png)
* **Title:** 10-Category Protocol Quality Audit Matrix
* **Carousel Headline:** *The Barn Door Protocol: A Systematic Framework for AI Safety & Reliability*
* **Classification:** Formatted QA Audit Report.
* **Verdict:** Qualified Pass for Controlled Local Single-User Use Only.
* **Recommended Caption:**
  > "No unverified claims. The Barn Door Protocol systematically audits 10 critical dimensions: Implementation, TDD, Unit, Integration, Security (CWE-1236 CSV injection, prompt injection escaping), Multi-User Concurrency, Negative Testing, and Performance. Qualified for controlled local single-user use."

---

### Slide 9: GenAI Quality Engineering & Evaluation Matrix
* **File:** [`09_genai_testing_report.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/09_genai_testing_report.png)
* **Title:** Methodological Rigor & Evaluation Benchmarks
* **Carousel Headline:** *Separating Fact from Hype: Methodological Tiers in GenAI Evaluation*
* **Classification:** GenAI Evaluation Benchmark Report.
* **Metrics:** 100% structured compliance, 100% numerical accuracy, 0% citation hallucination rate, and zero unauthorized API spend ($0.00).
* **Recommended Caption:**
  > "Engineering integrity in AI evaluation: strictly distinguishing deterministic tests, mocked unit tests, offline fallback evaluations, and live API smoke tests. 100% structured compliance, 100% numerical accuracy, 0% citation hallucination rate, and zero unauthorized API spend."

---

### Slide 10: GitHub Release & MIT License
* **File:** [`10_github_release_mit_license.png`](file:///Users/anirudhasaxena/Downloads/Antigravity-Projects/customer-feedback-intelligence/linkedin_portfolio_v3/10_github_release_mit_license.png)
* **Title:** Open Source Release & License Verification
* **Carousel Headline:** *Controlled Local Release: v3.0.0 Release with MIT License*
* **Classification:** Repository Release Metadata & License Verification.
* **Recommended Caption:**
  > "Clean architecture, transparent documentation, and verified release packaging. Customer Feedback Intelligence v3.0.0 is packaged under the permissive MIT License with clean SHA-256 release checksums, complete documentation, and zero credential leakage."

---

## 2. Screenshot Manifest & Technical Details

| File Name | Dimensions | Format | Content Source | Visible Content Verification |
|---|---|---|---|---|
| `01_main_analytics_dashboard.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Dashboard | Overview KPIs, sentiment & topic breakdowns |
| `02_feedback_classification_prioritization.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Dashboard | Priority table, status badges, PriorityScore 18–100 |
| `03_executive_insights_recommendations.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Dashboard | Strategic Executive Briefing & Action Roadmap |
| `04_genai_feedback_assistant_query.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Q&A | Billing question, actual answer, citations & recommendations |
| `05_deterministic_numerical_accuracy.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Q&A | Exact counts: 16 Critical, 106 High, 122 HC, 321 Total |
| `06_qa_test_scenario_generation.png` | 1920 × 993 | PNG (RGB) | Live Streamlit Q&A | Generated QA test scenarios, citations, engine badge |
| `07_automated_pytest_results.png` | 1920 × 993 | PNG (RGB) | Raw Terminal Output | 157-test pytest -v execution (paths sanitized) |
| `08_barn_door_protocol_qa_report.png` | 1920 × 993 | PNG (RGB) | Formatted QA Report | 10-category audit matrix & Qualified Pass verdict |
| `09_genai_testing_report.png` | 1920 × 993 | PNG (RGB) | Formatted Eval Report | Methodological tiers, metrics & smoke test audit |
| `10_github_release_mit_license.png` | 1920 × 993 | PNG (RGB) | Release Metadata | Commit `543a241`, v3.0.0 tag, MIT License legal text |
