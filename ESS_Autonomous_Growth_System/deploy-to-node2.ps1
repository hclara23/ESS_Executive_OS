# ESS - Autonomous Growth System Deployment Script
# Targets: botd2 (192.168.1.25)

$RemoteIP = "192.168.1.25"
$RemoteUser = "morningstar"
$RemoteDir = "/opt/ess-ags"

Write-Host "Creating remote directory $RemoteDir on $RemoteIP..." -ForegroundColor Cyan
ssh "${RemoteUser}@${RemoteIP}" "sudo mkdir -p $RemoteDir && sudo chown ${RemoteUser}:${RemoteUser} $RemoteDir"

Write-Host "Transferring files to $RemoteIP..." -ForegroundColor Cyan

# Transfer directories
scp -r api "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp -r db "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp -r worker "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp -r n8n "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp -r nginx "${RemoteUser}@${RemoteIP}:${RemoteDir}/"

# Transfer core files
scp docker-compose.yml "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp .env "${RemoteUser}@${RemoteIP}:${RemoteDir}/"
scp .gitignore "${RemoteUser}@${RemoteIP}:${RemoteDir}/"

Write-Host "Deployment complete! Files are now on the server." -ForegroundColor Green
Write-Host "`nTo start the system, SSH into the server and run:" -ForegroundColor Yellow
Write-Host "cd $RemoteDir"
Write-Host "docker compose up -d --build"
