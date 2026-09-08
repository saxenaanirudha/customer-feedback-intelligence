# Customer Feedback Intelligence System

An AI-powered customer feedback analysis platform that transforms raw customer feedback into structured, prioritized, and actionable business insights.

## Business Problem

Organizations receive large volumes of customer feedback. Manually reviewing every feedback item to understand customer sentiment, identify the issue, determine urgency, and prioritize action can be time-consuming and inconsistent.

This project automates that process and helps business teams quickly identify the customer issues that require attention.

## Objective

The objective of this project is to:

- Automate customer feedback analysis
- Reduce manual review effort
- Identify sentiment, topic, and urgency
- Prioritize high-impact customer issues
- Provide business analytics through an interactive dashboard
- Generate AI-assisted executive insights and recommendations

## How It Works

```text
Raw Customer Feedback
        |
        v
Data Cleaning & Validation
        |
        v
AI / Hybrid Classification
        |
        v
Sentiment + Topic + Urgency
        |
        v
Business Priority Scoring
        |
        v
Analytics & Pain Point Detection
        |
        v
Streamlit Dashboard
        |
        v
AI Executive Insights
```

## Key Features

### 1. Data Cleaning and Validation

The preprocessing pipeline validates and cleans raw customer feedback, including:

- Duplicate feedback IDs
- Missing feedback text
- Invalid ratings
- Invalid dates
- Invalid customer types
- Unnecessary whitespace

### 2. Intelligent Feedback Classification

Each feedback item is classified into:

**Sentiment**
- Positive
- Neutral
- Negative

**Topic**
- Billing
- Pricing
- Performance
- Product Features
- Customer Support
- UI/UX
- Other

**Urgency**
- Low
- Medium
- High
- Critical

The application supports AI-powered classification with fallback logic to keep the processing workflow reliable.

### 3. Business Priority Scoring

The system calculates an explainable priority score using business factors such as:

- Urgency
- Customer type
- Sentiment
- Rating

Each feedback receives:

- Priority Score
- Priority Level
- Priority Reason

This helps teams identify which customer issues should be investigated first.

### 4. Business Analytics Dashboard

The interactive Streamlit dashboard provides:

- Executive KPIs
- Sentiment analysis
- Topic analysis
- Priority distribution
- Customer segment analysis
- Feedback trends
- Top customer pain points
- High-priority issue exploration
- Feedback search and filtering

### 5. AI Executive Insights

Instead of sending the complete raw dataset directly to the LLM, the application first generates structured analytics.

Relevant KPIs, pain points, customer segment risks, and representative feedback are then used to generate:

- Executive summaries
- Key risks
- Recommended actions
- Priority areas
- Watch items

This approach reduces unnecessary LLM usage while keeping recommendations grounded in calculated analytics.

## Project Structure

```text
customer-feedback-intelligence/
|
|-- data/
|   `-- feedback.csv
|
|-- src/
|   |-- preprocessing.py
|   |-- classifier.py
|   |-- priority.py
|   |-- insights.py
|   `-- executive_insights.py
|
|-- dashboard/
|   `-- app.py
|
|-- output/
|
|-- tests/
|
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- main.py
`-- README.md
```

## Technology Stack

- Python
- Pandas
- Streamlit
- Plotly
- OpenAI API
- Pydantic

## Installation

### 1. Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd customer-feedback-intelligence
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as the template.

```env
OPENAI_API_KEY=your_api_key_here
```

Never commit your actual `.env` file or API key to GitHub.

## Running the Project

To run the complete processing pipeline:

```bash
python main.py --full
```

To launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## Success Metrics

The business impact of the solution can be evaluated using KPIs such as:

- Feedback processing time
- Manual effort reduction
- Classification accuracy
- Priority identification accuracy
- Percentage of feedback successfully processed
- Time required to identify critical customer issues

## Future Improvements

Potential production enhancements include:

- CRM and customer support platform integrations
- Database-based feedback storage
- User authentication and role-based access
- Automated background alerts
- Model performance monitoring
- Cloud deployment
- Audit logging

## Security

Sensitive credentials are stored using environment variables.

The `.env` file and virtual environment are excluded from Git using `.gitignore`.

## Project Purpose

This project demonstrates an end-to-end approach to converting unstructured customer feedback into structured business intelligence using Python, analytics, automation, and Generative AI.