# RevPilot

## Problem

Businesses often know that revenue/profit changed but determining the actual root cause requires manually investigating multiple sources of business data.

## Intended User

Business owners and finance/operations teams.

## Goal

Build an agentic workflow that investigates business performance, identifies likely root causes, verifies those conclusions against evidence, and produces actionable recommendations.

## Current Status

**Step 1 — Project Foundation**

Agents have NOT been implemented yet. This is the foundational setup for the backend and project structure.

## Project Structure

```
revpilot/
├── backend/            # FastAPI backend (and future agent logic)
│   ├── app/            # Application code
│   └── requirements.txt
├── agents/             # Future specific agent definitions
├── tools/              # Future tools for agents
├── data/               # Data access and schemas
├── evaluation/         # System evaluation scripts
├── tests/              # Automated tests
├── frontend/           # Future frontend (e.g. Next.js)
├── .env.example        # Environment variable templates
├── docker-compose.yml  # Docker orchestration
└── README.md           # Project documentation
```

## Prerequisites

- Python 3.13+
- Node.js (for future frontend)
- Git
- Docker (optional)

## Setup Instructions

### 1. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

### 3. Start the Backend

```bash
uvicorn backend.app.main:app --reload
```
The server will start at `http://127.0.0.1:8000`.

### 4. Test the API

To verify the backend is running, check the health endpoint:
```bash
curl http://127.0.0.1:8000/health
```

Or run the automated tests:
```bash
pytest tests/
```
