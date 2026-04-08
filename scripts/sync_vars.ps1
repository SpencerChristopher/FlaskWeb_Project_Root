# scripts/sync_vars.ps1
# Pulls GitHub Repository Variables and saves them to .env.vars for local development.

$outputFile = ".env.vars"
Write-Host "Fetching variables from SpencerChristopher/FlaskWeb_Project_Root..."

# Fetch repo-level variables
$vars = gh variable list --json name,value | ConvertFrom-Json

# Local overrides that must remain editable for local dev/testing
$overrideKeys = @(
    "TALISMAN_FORCE_HTTPS",
    "TURNSTILE_ENABLED",
    "TURNSTILE_LOGIN_ENABLED",
    "FLASK_ENV",
    "JWT_COOKIE_SECURE",
    "LOG_LEVEL"
)

$defaultOverrides = @{
    "TALISMAN_FORCE_HTTPS" = "false"
    "TURNSTILE_ENABLED" = "false"
    "TURNSTILE_LOGIN_ENABLED" = "false"
    "FLASK_ENV" = "development"
    "JWT_COOKIE_SECURE" = "false"
    "LOG_LEVEL" = "DEBUG"
}

# Preserve any existing local overrides already in .env.vars
$existingVars = @{}
if (Test-Path $outputFile) {
    Get-Content $outputFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2]
            if (-not [string]::IsNullOrWhiteSpace($key)) {
                $existingVars[$key] = $value
            }
        }
    }
}

if ($vars.Count -eq 0) {
    Write-Host "No variables found in repository."
    exit 0
}

# Write to file (repo vars + preserved local overrides)
$lines = New-Object System.Collections.Generic.List[string]
$writtenKeys = New-Object System.Collections.Generic.HashSet[string]

foreach ($var in $vars) {
    $name = $var.name
    $value = $var.value

    if ($overrideKeys -contains $name) {
        if ($existingVars.ContainsKey($name)) {
            $value = $existingVars[$name]
            Write-Host "Preserving local override: $name"
        } elseif ($defaultOverrides.ContainsKey($name)) {
            $value = $defaultOverrides[$name]
            Write-Host "Applying local default override: $name"
        } else {
            Write-Host "Skipping local override (no default): $name"
            continue
        }
    }

    $lines.Add("$name=$value")
    $writtenKeys.Add($name) | Out-Null
}

# Ensure local overrides exist even if they are not repo vars
foreach ($key in $overrideKeys) {
    if (-not $writtenKeys.Contains($key)) {
        if ($existingVars.ContainsKey($key)) {
            $lines.Add("$key=$($existingVars[$key])")
            Write-Host "Preserving local override: $key"
        } elseif ($defaultOverrides.ContainsKey($key)) {
            $lines.Add("$key=$($defaultOverrides[$key])")
            Write-Host "Applying local default override: $key"
        }
    }
}

$lines | Set-Content $outputFile

Write-Host "Successfully synced $($vars.Count) variables to $outputFile"
