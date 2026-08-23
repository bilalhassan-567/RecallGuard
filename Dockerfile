# RecallGuard dashboard — Cloud Run container.
#
# Build context is the repo root (so it can COPY agents/ as-is, matching the sys.path
# tricks in agents/dashboard/server.py). Build and run locally today — this needs no
# GCP project or billing to test, but does need Docker Desktop installed (not yet on the
# dev machine as of 2026-08-23 — optional, since `gcloud run deploy --source .` builds
# remotely via Cloud Build and doesn't need local Docker at all):
#
#   docker build -t recallguard-dashboard .
#   docker run --rm -p 8080:8080 --env-file agents/.env recallguard-dashboard
#   open http://localhost:8080/
#
# Deploy once GCP billing is unblocked (see docs/GCP_SETUP.md, Part B):
#
#   gcloud run deploy recallguard-dashboard --source . --region us-central1 \
#     --allow-unauthenticated --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=FALSE

FROM python:3.12-slim

WORKDIR /app

# Only agents/ ships to the container — docs/, .git/, .venv/, .idea/ are dev-only.
COPY agents/requirements.txt ./agents/requirements.txt
RUN pip install --no-cache-dir -r agents/requirements.txt

COPY agents/ ./agents/

WORKDIR /app/agents

# Cloud Run sets $PORT (defaults to 8080) and expects the container to listen on it —
# do not hardcode 8000 here even though that's the local-dev default in the README.
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn dashboard.server:app --host 0.0.0.0 --port ${PORT}"]
