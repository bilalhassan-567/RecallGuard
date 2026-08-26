# agents/ — quick start

Everything below runs with just a free Gemini API key — no GCP project or billing
account needed locally. The same code also runs live on Google Cloud today (Cloud Run
+ Cloud Functions + Firestore + Pub/Sub + Cloud Scheduler) — see the root
[`README.md`](../README.md) for the live URL and `docs/GCP_SETUP.md` for that side.

## Setup

```
cd agents
pip install -r requirements.txt
cp .env.example .env
```

Then open `agents/.env` and paste in a key from https://aistudio.google.com ("Get API
key" → create a key — no billing account required).

## 1. Confirm the key works

```
python test_gemini.py
```

Should print a one-line response from Gemini plus a token count. If this fails, the key
or `.env` setup is the problem — fix that before anything else.

## 2. Run the full pipeline

```
python run_matching_demo.py
```

Ingestion → matching → action, end to end, against live openFDA recall data. Costs
real Gemini quota (free tier is 20 requests/day per model — see
`docs/RISK_REGISTER.md`), so pace repeated runs.

## 3. Run the dashboard

```
uvicorn dashboard.server:app --reload --port 8010
```

Open http://127.0.0.1:8010/ — reads whatever step 2 (or an invoice you upload directly
through the dashboard's own Invoices panel) produced. See
[`dashboard/README.md`](dashboard/README.md) for what's actually wired up.

## 4. Run the test suite

```
cd ingestion && python -m unittest discover -p "test_*.py" && cd ..
cd invoices && python -m unittest test_csv_parser test_invoice_store && cd ..   # skips the one live-network test
cd action && python -m unittest discover -p "test_*.py" && cd ..
cd dashboard && python -m unittest discover -p "test_*.py" && cd ..
cd experiment && python -m unittest discover -p "test_*.py" && cd ..
python -m unittest test_storage
```

All offline, no API key or network needed, no Gemini quota consumed.

## 5. Try the failure-injection demo

```
python demo_failure_injection.py
```

A real (not mocked) OS-level failure and recovery in the Action Agent's PDF export
step — zero Gemini cost, safe to run repeatedly.

## ADK hello-world (optional, not part of the deployed pipeline)

```
adk run hello_agent
```

or `adk web` for the browser dev UI. If ADK can't find the API key, copy `.env` into
the agent's own folder too: `cp .env hello_agent/.env` (gitignored the same way).

## Layout

| Dir | What |
|---|---|
| `ingestion/` | openFDA/FSIS clients + normalization |
| `invoices/` | CSV parser, Gemini-vision photo parser, `invoice_store.py` (the real Invoices entity) |
| `matching/` | The Gemini fuzzy-matching agent |
| `action/` | Checklist/notification/compliance-PDF generation — no LLM calls, no network sends |
| `dashboard/` | FastAPI backend + the single-file frontend, live on Cloud Run |
| `experiment/` | The N=30 evaluation harness (agent + human baseline + naive comparison) |
| `main.py` | Cloud Function entry points for the live Pub/Sub event backbone |
