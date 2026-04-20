param(
  [string]$Server = $env:SERVER,
  [int]$Port = $(if ($env:ELIO_SERVER_PORT) { [int]$env:ELIO_SERVER_PORT } else { 22 }),
  [string]$RemotePath = $(if ($env:ELIO_SERVER_PATH) { $env:ELIO_SERVER_PATH } else { "~/elio" }),
  [int]$ApiPort = $(if ($env:ELIO_API_PORT) { [int]$env:ELIO_API_PORT } else { 8000 }),
  [int]$OllamaPort = $(if ($env:ELIO_OLLAMA_PORT) { [int]$env:ELIO_OLLAMA_PORT } else { 11434 }),
  [int]$PostgresPort = $(if ($env:ELIO_POSTGRES_PORT) { [int]$env:ELIO_POSTGRES_PORT } else { 5432 }),
  [string]$ComposeProjectName = $(if ($env:COMPOSE_PROJECT_NAME) { $env:COMPOSE_PROJECT_NAME } else { "elio" }),
  [string]$EdgeNetwork = $(if ($env:EDGE_NETWORK) { $env:EDGE_NETWORK } else { "platform_edge" }),
  [switch]$WithXtts,
  [switch]$SharedHost,
  [switch]$SyncEnv,
  [switch]$SyncVoices,
  [switch]$SkipModelBootstrap,
  [switch]$SkipSeed,
  [switch]$SkipPrewarm
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$dotEnvPath = Join-Path $repoRoot ".env"
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$bundlePath = Join-Path $env:TEMP "elio-$timestamp.tar.gz"
$serverEnvPath = Join-Path $env:TEMP "elio-server-$timestamp.env"
$remoteBundle = "$RemotePath/elio-$timestamp.tar.gz"

function Get-DotEnvValue {
  param(
    [string]$Path,
    [string]$Name
  )

  if (-not (Test-Path $Path)) {
    return $null
  }

  $line = Select-String -Path $Path -Pattern "^$([regex]::Escape($Name))=(.*)$" | Select-Object -First 1
  if (-not $line) {
    return $null
  }

  return $line.Matches[0].Groups[1].Value
}

if (-not $PSBoundParameters.ContainsKey("Server") -and -not $env:SERVER) {
  $Server = Get-DotEnvValue -Path $dotEnvPath -Name "SERVER"
}
if (-not $PSBoundParameters.ContainsKey("Port") -and -not $env:ELIO_SERVER_PORT) {
  $dotEnvServerPort = Get-DotEnvValue -Path $dotEnvPath -Name "ELIO_SERVER_PORT"
  if ($dotEnvServerPort) {
    $Port = [int]$dotEnvServerPort
  }
}
if (-not $PSBoundParameters.ContainsKey("RemotePath") -and -not $env:ELIO_SERVER_PATH) {
  $dotEnvServerPath = Get-DotEnvValue -Path $dotEnvPath -Name "ELIO_SERVER_PATH"
  if ($dotEnvServerPath) {
    $RemotePath = $dotEnvServerPath
  }
}
if (-not $PSBoundParameters.ContainsKey("ApiPort") -and -not $env:ELIO_API_PORT) {
  $dotEnvApiPort = Get-DotEnvValue -Path $dotEnvPath -Name "ELIO_API_PORT"
  if ($dotEnvApiPort) {
    $ApiPort = [int]$dotEnvApiPort
  }
}
if (-not $PSBoundParameters.ContainsKey("OllamaPort") -and -not $env:ELIO_OLLAMA_PORT) {
  $dotEnvOllamaPort = Get-DotEnvValue -Path $dotEnvPath -Name "ELIO_OLLAMA_PORT"
  if ($dotEnvOllamaPort) {
    $OllamaPort = [int]$dotEnvOllamaPort
  }
}
if (-not $PSBoundParameters.ContainsKey("PostgresPort") -and -not $env:ELIO_POSTGRES_PORT) {
  $dotEnvPostgresPort = Get-DotEnvValue -Path $dotEnvPath -Name "ELIO_POSTGRES_PORT"
  if ($dotEnvPostgresPort) {
    $PostgresPort = [int]$dotEnvPostgresPort
  }
}
if (-not $PSBoundParameters.ContainsKey("ComposeProjectName") -and -not $env:COMPOSE_PROJECT_NAME) {
  $dotEnvProjectName = Get-DotEnvValue -Path $dotEnvPath -Name "COMPOSE_PROJECT_NAME"
  if ($dotEnvProjectName) {
    $ComposeProjectName = $dotEnvProjectName
  }
}
if (-not $PSBoundParameters.ContainsKey("EdgeNetwork") -and -not $env:EDGE_NETWORK) {
  $dotEnvEdgeNetwork = Get-DotEnvValue -Path $dotEnvPath -Name "EDGE_NETWORK"
  if ($dotEnvEdgeNetwork) {
    $EdgeNetwork = $dotEnvEdgeNetwork
  }
}

if (-not $Server) {
  throw "Missing target server. Set the SERVER env var or pass -Server user@host."
}

$excludeArgs = @(
  "--exclude=.git",
  "--exclude=.venv",
  "--exclude=venv",
  "--exclude=__pycache__",
  "--exclude=.pytest_cache",
  "--exclude=.cache",
  "--exclude=.firebase",
  "--exclude=.github",
  "--exclude=.env",
  "--exclude=voices/xtts"
)

Push-Location $repoRoot
try {
  if (Test-Path $bundlePath) {
    Remove-Item $bundlePath -Force
  }

  tar.exe -czf $bundlePath @excludeArgs .

  ssh -p $Port $Server "mkdir -p $RemotePath"
  scp -P $Port $bundlePath "${Server}:${remoteBundle}"

  ssh -p $Port $Server "cd $RemotePath && tar -xzf $(Split-Path $remoteBundle -Leaf) && rm -f $(Split-Path $remoteBundle -Leaf)"

  if ($SyncEnv) {
    $envPath = Join-Path $repoRoot ".env"
    if (-not (Test-Path $envPath)) {
      throw "SyncEnv was requested but .env was not found at $envPath."
    }
    & .\.venv\Scripts\python.exe .\tools\render_server_env.py --source .env --output $serverEnvPath --set "ELIO_API_PORT=$ApiPort" --set "ELIO_OLLAMA_PORT=$OllamaPort" --set "ELIO_POSTGRES_PORT=$PostgresPort" --set "COMPOSE_PROJECT_NAME=$ComposeProjectName" --set "EDGE_NETWORK=$EdgeNetwork"
    scp -P $Port $serverEnvPath "${Server}:${RemotePath}/.env"
  }

  if ($WithXtts -or $SyncVoices) {
    $voicesPath = Join-Path $repoRoot "voices\\xtts"
    if (Test-Path $voicesPath) {
      ssh -p $Port $Server "mkdir -p $RemotePath/voices"
      scp -P $Port -r $voicesPath "${Server}:${RemotePath}/voices/"
    }
  }

  $withXttsValue = if ($WithXtts) { "1" } else { "0" }
  $sharedHostValue = if ($SharedHost) { "1" } else { "0" }
  $bootstrapModelsValue = if ($SkipModelBootstrap) { "0" } else { "1" }
  $seedValue = if ($SkipSeed) { "0" } else { "1" }
  $prewarmValue = if ($SkipPrewarm) { "0" } else { "1" }

  if ($SharedHost) {
    ssh -p $Port $Server "docker network inspect $EdgeNetwork >/dev/null 2>&1 || docker network create $EdgeNetwork"
  }

  $remoteCommand = @(
    "cd $RemotePath",
    "chmod +x tools/server_bootstrap.sh",
    "COMPOSE_PROJECT_NAME=$ComposeProjectName EDGE_NETWORK=$EdgeNetwork SHARED_HOST=$sharedHostValue WITH_XTTS=$withXttsValue BOOTSTRAP_MODELS=$bootstrapModelsValue SEED_ADMIN=$seedValue PREWARM_STACK=$prewarmValue bash tools/server_bootstrap.sh `"$RemotePath`""
  ) -join " && "

  ssh -p $Port $Server $remoteCommand
}
finally {
  Pop-Location
  if (Test-Path $bundlePath) {
    Remove-Item $bundlePath -Force
  }
  if (Test-Path $serverEnvPath) {
    Remove-Item $serverEnvPath -Force
  }
}
