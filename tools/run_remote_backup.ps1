param(
  [string]$Server = $env:SERVER,
  [int]$Port = $(if ($env:ELIO_SERVER_PORT) { [int]$env:ELIO_SERVER_PORT } else { 22 }),
  [string]$RemotePath = $(if ($env:ELIO_SERVER_PATH) { $env:ELIO_SERVER_PATH } else { "~/elio" }),
  [string]$LocalOutput = ".\backups",
  [switch]$Download
)

$ErrorActionPreference = "Stop"

if (-not $Server) {
  throw "Missing target server. Set SERVER or pass -Server."
}

$result = ssh -p $Port $Server "cd $RemotePath && chmod +x tools/server_backup.sh && bash tools/server_backup.sh `"$RemotePath`""
$backupLine = $result | Select-String '^BACKUP_PATH=' | Select-Object -Last 1
if (-not $backupLine) {
  throw "Remote backup did not return a backup path."
}

$remoteBackupPath = $backupLine.ToString().Split('=', 2)[1]
Write-Output "Remote backup created: $remoteBackupPath"

if ($Download) {
  New-Item -ItemType Directory -Force -Path $LocalOutput | Out-Null
  scp -P $Port -r "${Server}:${remoteBackupPath}" $LocalOutput
}
