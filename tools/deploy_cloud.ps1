# Deployment Script for Elio API to Google Cloud Run

$PROJECT_ID = Read-Host "Enter your Google Cloud Project ID"
$REGION = "us-central1"
$SERVICE_NAME = "elio-api"

Write-Host "Enabling required Google APIs..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project $PROJECT_ID

Write-Host "Building and pushing image..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --project $PROJECT_ID

Write-Host "Collecting runtime configuration..."
$ELIO_JWT_SECRET = Read-Host "Enter ELIO_JWT_SECRET"
$ELIO_PG_URI = Read-Host "Enter ELIO_PG_URI"
$ELIO_ALLOWED_ORIGINS = Read-Host "Enter ELIO_ALLOWED_ORIGINS"
$OPENAI_API_KEY = Read-Host "Enter OPENAI_API_KEY (leave blank for local-only model routing)"
$ELIO_LLM_MODE = Read-Host "Enter ELIO_LLM_MODE (default hybrid)"
if (-not $ELIO_LLM_MODE) { $ELIO_LLM_MODE = "hybrid" }

$envVars = @(
    "ELIO_JWT_SECRET=$ELIO_JWT_SECRET"
    "ELIO_PG_URI=$ELIO_PG_URI"
    "ELIO_ALLOWED_ORIGINS=$ELIO_ALLOWED_ORIGINS"
    "ELIO_LLM_MODE=$ELIO_LLM_MODE"
)

if ($OPENAI_API_KEY) {
    $envVars += "OPENAI_API_KEY=$OPENAI_API_KEY"
}

Write-Host "Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME `
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME `
    --region $REGION `
    --platform managed `
    --allow-unauthenticated `
    --set-env-vars ($envVars -join ",") `
    --project $PROJECT_ID

$URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)' --project $PROJECT_ID
Write-Host "Deployment complete."
Write-Host "API URL: $URL"
Write-Host "Runtime inspection: $URL/system/runtime"
