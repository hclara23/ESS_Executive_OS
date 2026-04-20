param(
  [string]$Server = $env:SERVER,
  [int]$Port = $(if ($env:ELIO_SERVER_PORT) { [int]$env:ELIO_SERVER_PORT } else { 22 }),
  [string]$RemotePath = $(if ($env:ELIO_SERVER_PATH) { $env:ELIO_SERVER_PATH } else { "~/elio" }),
  [string]$BaseUrl = $(if ($env:ELIO_API_PORT) { "http://127.0.0.1:$($env:ELIO_API_PORT)" } else { "http://127.0.0.1:8000" }),
  [string]$OutFile = ""
)

$ErrorActionPreference = "Stop"

if (-not $Server) {
  throw "Missing target server. Set SERVER or pass -Server."
}

$sections = @()
$sections += "== host =="
$sections += ssh -p $Port $Server "hostname && uptime && df -h / && free -h"
$sections += ""
$sections += "== docker compose ps =="
$sections += ssh -p $Port $Server "cd $RemotePath && docker compose ps"
$sections += ""
$sections += "== docker stats =="
$sections += ssh -p $Port $Server "docker stats --no-stream"
$sections += ""
$sections += "== runtime =="
$sections += (& .\.venv\Scripts\python.exe .\tools\remote_runtime_snapshot.py --base-url $BaseUrl)

$content = ($sections -join [Environment]::NewLine)
if ($OutFile) {
  Set-Content -Path $OutFile -Value $content -Encoding UTF8
} else {
  Write-Output $content
}
