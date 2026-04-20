param(
    [string[]]$Models = @(
        "qwen3:8b",
        "nomic-embed-text",
        "qwen2.5vl:7b"
    ),
    [switch]$IncludeLargeChatModel
)

$ErrorActionPreference = "Stop"

if ($IncludeLargeChatModel -and -not ($Models -contains "qwen3:14b")) {
    $Models = @("qwen3:14b") + $Models
}

Write-Host "Starting Ollama service..."
docker compose up -d ollama | Out-Null

$containerId = (docker compose ps -q ollama).Trim()
if (-not $containerId) {
    throw "Could not resolve the Ollama container id."
}

foreach ($model in $Models) {
    Write-Host "Pulling $model..."
    docker exec $containerId ollama pull $model
}

Write-Host "Local model bootstrap complete."
