param(
  [Parameter(Mandatory = $true)][string]$AdminUser,
  [Parameter(Mandatory = $true)][string]$AdminPass,
  [string]$EmailId,
  [string]$EmailPass
)

$argsList = @(
  "tools/seed_admin.py",
  "--admin-user", $AdminUser,
  "--admin-pass", $AdminPass
)

if ($EmailId -and $EmailPass) {
  $argsList += @("--email-id", $EmailId, "--email-pass", $EmailPass)
}

python @argsList
