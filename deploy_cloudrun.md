# Deploying the FastAPI server to Cloud Run (example)

Prereqs:
- Install and authenticate the Google Cloud SDK: `gcloud auth login` and `gcloud config set project PROJECT_ID`
- Enable APIs: Cloud Run, Cloud Build, Artifact Registry (or Container Registry), Secret Manager (optional)

Build and push locally (Docker + gcloud):

```bash
# build image
docker build -t gcr.io/PROJECT_ID/elio-api:latest -f server/Dockerfile .

# push image
docker push gcr.io/PROJECT_ID/elio-api:latest

# deploy to Cloud Run
gcloud run deploy elio-api \
  --image gcr.io/PROJECT_ID/elio-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "ELIO_JWT_SECRET=YOUR_SECRET,ELIO_SUPERUSER_EMAIL=you@example.com"
```

Recommended CI (Cloud Build): the included `cloudbuild.yaml` will build, push and deploy via Cloud Build on commits to the repository.

Notes:
- Use Secret Manager and `gcloud run services update --update-secrets` or Cloud Build substitutions for production secrets instead of `--set-env-vars` on the command line.
- After Cloud Run is deployed, configure `firebase.json` rewrites to forward `/api/**` and `/wiscore/**` to the Cloud Run service so the frontend can call `/api/...` without CORS changes.
