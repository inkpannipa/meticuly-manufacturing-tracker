# Meticuly Flow

A manufacturing process tracking prototype built for the Software Engineer Preliminary Assignment. It tracks production orders across a configurable multi-step workflow and records resource consumption at each transition.

## Stack

- React 19 + Vite frontend
- Python 3.12 + FastAPI + SQLAlchemy backend
- PostgreSQL 16 database
- Docker Compose for local orchestration

## Run locally

Prerequisite: Docker Desktop with Docker Compose. Make sure Docker Desktop shows
`Engine running` before starting the project.

```bash
docker compose up --build
```

Open `http://localhost:5173`. API documentation is available at `http://localhost:8000/docs`.

The database and sample production data are created automatically on first launch. To start fresh, run `docker compose down -v` and then start again.

## Core workflow

1. Create an order with product, customer, quantity, and priority.
2. It enters Material Prep automatically.
3. Use the arrow action on an active order to record resource consumption and advance it.
4. Orders move through Machining, Quality Check, and Packaging in sequence.
5. Advancing after Packaging completes the order.

## Design notes

- Order transitions and resource records are committed in one database transaction.
- A history row records when an order entered and exited each stage.
- The API validates positive quantities, priorities, resource IDs, and completed-order transitions.
- The dashboard aggregates current work-in-progress and resource usage from source records.
- Seeded data makes the prototype immediately explorable.

## Development without Docker

Set `DATABASE_URL` to a PostgreSQL instance, then:

```bash
cd backend
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

## Verification

Run the backend tests from the repository root:

```bash
python -m pytest backend/tests -q
```

Build the production frontend:

```bash
cd frontend
npm install
npm run build
```

## Repository structure

```text
backend/                FastAPI application, data models, and tests
frontend/               React application and production Nginx image
output/pdf/             One-page assignment summary for submission
docker-compose.yml      PostgreSQL, API, and web orchestration
ASSIGNMENT_SUMMARY.md   Editable source of the written summary
```

## AI-assisted development disclosure

AI assistance was used to help interpret the brief, scaffold the architecture, generate implementation code, and review the user journey. The implementation and behavior should still be reviewed as normal engineering work; no production or confidential customer data is included.

## License and usage

This repository is an assessment submission prepared for Meticuly Co., Ltd. It
is provided for recruitment evaluation and is not intended as a production
medical or manufacturing system.

