# scripts/sync_vars.ps1
# Pulls GitHub Repository Variables and saves them to .env.vars for local development.

$outputFile = ".env.vars"
Write-Host "Fetching variables from SpencerChristopher/FlaskWeb_Project_Root..."

# Fetch repo-level variables
$vars = gh variable list --json name,value | ConvertFrom-Json

if ($vars.Count -eq 0) {
    Write-Host "No variables found in repository."
    exit 0
}

# Write to file
$vars | ForEach-Object {
    "$($_.name)=$($_.value)"
} | Set-Content $outputFile

Write-Host "Successfully synced $($vars.Count) variables to $outputFile"
