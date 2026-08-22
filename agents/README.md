# agents/ — quick start

Local dev setup that works with just a free Gemini API key — no GCP project or billing
account needed for this part. Once GCP billing is unblocked, the same code switches to
Vertex AI by flipping one env var (see `.env.example`).

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
or `.env` setup is the problem — fix that before touching ADK.

## 2. Run the hello-world ADK agent

```
adk run hello_agent
```

or, for the browser dev UI:

```
adk web
```

**If ADK can't find the API key:** the ADK CLI looks for `.env` inside the agent's own
folder first. If `adk run`/`adk web` complains about a missing key even though
`agents/.env` exists, copy it into the agent folder too: `cp .env hello_agent/.env`
(gitignored the same way).

## What's next

This is Phase 1 scaffolding only (`docs/PHASES.md`). The real Recall Monitor / Matching /
Action agents get built out from here once the GCP billing blocker clears (see
`docs/PLAN.md` and `docs/RISK_REGISTER.md`).
