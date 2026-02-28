param(
    [switch]$RunAct,
    [switch]$SkipAudit,
    [switch]$SkipCloud
)

$ErrorActionPreference = "Stop"

function Require-Command($name, [switch]$Optional) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        if (-not $Optional) {
            Write-Host "Error: Required tool '$name' is not installed." -ForegroundColor Red
        }
        return $false
    }
    return $true
}

Write-Host "`n--- Preflight Security & Integrity Checks (PowerShell) ---" -ForegroundColor Cyan

# [1/7] Tool Check
Write-Host "[1/7] Verifying required tools..."
$tools = @("poetry", "docker", "gh")
foreach ($tool in $tools) {
    if (-not (Require-Command $tool)) { 
        if ($tool -eq "gh") {
            Write-Host "Warning: GitHub CLI (gh) not found. Cloud-aware checks will be skipped." -ForegroundColor Yellow
        } else {
            exit 1 
        }
    }
}

# [2/7] Cloud State Validation (GitHub CLI)
if (-not $SkipCloud -and (Require-Command "gh" -Optional)) {
    Write-Host "[2/7] Validating Cloud State (GitHub)..."
    
    # Check Runner Status
    try {
        $runners = gh api repos/:owner/:repo/actions/runners | ConvertFrom-Json
        $wslRunner = $runners.runners | Where-Object { $_.labels.name -contains "wsl-staging" }
        
        if ($null -eq $wslRunner) {
            Write-Host "Warning: No runner with label 'wsl-staging' found in GitHub." -ForegroundColor Yellow
        } elseif ($wslRunner.status -ne "online") {
            Write-Host "CRITICAL: WSL Staging runner is OFFLINE. Deployments will fail." -ForegroundColor Red
            if ($ConfirmPreference -ne "None") {
                $choice = Read-Host "Proceed anyway? (y/N)"
                if ($choice -ne "y") { exit 1 }
            }
        } else {
            Write-Host "Staging Runner: ONLINE" -ForegroundColor Green
        }
    } catch {
        Write-Host "Warning: Could not fetch runner status. Are you logged in to 'gh'?" -ForegroundColor Yellow
    }

    # Check Secret Existence (Names only)
    try {
        $remoteSecrets = gh secret list | ForEach-Object { $_.Split("`t")[0] }
        $requiredSecrets = @("SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD", "MONGO_ROOT_USER", "MONGO_ROOT_PASSWORD", "MONGO_APP_USER", "MONGO_APP_PASSWORD")
        
        foreach ($s in $requiredSecrets) {
            if ($s -notin $remoteSecrets) {
                Write-Host "MISSING SECRET: '$s' is required by CI but not found in GitHub." -ForegroundColor Red
                $missingSecret = $true
            }
        }
        if ($missingSecret) { exit 1 } else { Write-Host "GitHub Secrets: VERIFIED" -ForegroundColor Green }
    } catch {
        Write-Host "Warning: Could not fetch secret list." -ForegroundColor Yellow
    }
} else {
    Write-Host "[2/7] Skipping Cloud State Validation." -ForegroundColor Yellow
}

# [3/7] Security Audit (pip-audit)
Write-Host "[3/7] Running security audit..."
if ($SkipAudit) {
    Write-Host "Skipping audit as requested." -ForegroundColor Yellow
} elseif (Require-Command "pip-audit" -Optional) {
    poetry export --format=constraints.txt --output=constraints.txt --without-hashes
    try {
        pip-audit -r constraints.txt
        Write-Host "Security audit passed: No known vulnerabilities." -ForegroundColor Green
    } finally {
        if (Test-Path constraints.txt) { Remove-Item constraints.txt }
    }
} else {
    Write-Host "Warning: pip-audit not found. Skipping local dependency scan." -ForegroundColor Yellow
}

# [4/7] Lockfile Freshness
Write-Host "[4/7] Ensuring poetry.lock is up to date..."
poetry lock
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: poetry lock failed." -ForegroundColor Red
    exit 1
}

# [5/7] GitHub Actions Linting
Write-Host "[5/7] Linting GitHub Actions workflows..."
if (Require-Command "actionlint" -Optional) {
    & actionlint -color -format '{{.Filepath}}:{{.Line}}:{{.Column}}: {{.Message}}' ".github/workflows/*.yml"
} else {
    Write-Host "Warning: actionlint not found. Skipping workflow linting." -ForegroundColor Yellow
}

# [6/7] Local CI Simulation (Optional)
if ($RunAct) {
    Write-Host "[6/7] Running local workflow simulation (act)..."
    if (Require-Command "act" -Optional) {
        act -W .github/workflows/test-deploy.yml
    } else {
        Write-Host "Install act to run workflows locally, then re-run with -RunAct." -ForegroundColor Yellow
    }
} else {
    Write-Host "[6/7] Skipping local workflow simulation."
}

# [7/7] Docker Stack Build
Write-Host "[7/7] Verifying Docker stack build..."
docker compose --env-file .env build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker build failed." -ForegroundColor Red
    exit 1
}

Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Preflight complete. Local environment is healthy and secure.`n" -ForegroundColor Green
