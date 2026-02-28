param(
    [switch]$RunAct,
    [switch]$SkipAudit,
    [switch]$SkipCloud,
    [switch]$Verbose
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

# [1/6] Tool Check
Write-Host "[1/6] Verifying required tools..."
$tools = @("poetry", "docker")
foreach ($tool in $tools) {
    if (-not (Require-Command $tool)) { exit 1 }
}

# [2/6] Cloud State Validation (GitHub CLI)
if (-not $SkipCloud -and (Require-Command "gh" -Optional)) {
    Write-Host "[2/6] Validating Cloud State (GitHub)..."
    
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

    # Check Secret Existence
    try {
        $remoteSecrets = gh secret list | ForEach-Object { $_.Split("`t")[0] }
        $requiredSecrets = @("SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD", "MONGO_ROOT_USER", "MONGO_ROOT_PASSWORD", "MONGO_APP_USER", "MONGO_APP_PASSWORD")
        $missingSecret = $false
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
    Write-Host "[2/6] Skipping Cloud State Validation." -ForegroundColor Yellow
}

# [3/6] Containerized Validation (Lint & Audit)
Write-Host "[3/6] Running containerized lints and security audits (Silent)..."
if ($SkipAudit) {
    Write-Host "Skipping validation as requested." -ForegroundColor Yellow
} else {
    # Run docker build quietly, only showing error output unless -Verbose is passed
    if ($Verbose) {
        docker build --target validate .
    } else {
        docker build --target validate --quiet . > $null
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Containerized validation (lint/audit) failed. Run with -Verbose for details." -ForegroundColor Red
        exit 1
    }
    Write-Host "Containerized validation passed." -ForegroundColor Green
}

# [4/6] Lockfile Freshness
Write-Host "[4/6] Ensuring poetry.lock is up to date..."
poetry lock --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: poetry lock failed." -ForegroundColor Red
    exit 1
}

# [5/6] Local CI Simulation (Optional)
if ($RunAct) {
    Write-Host "[5/6] Running local workflow simulation (act)..."
    if (Require-Command "act" -Optional) {
        & act -W .github/workflows/test-deploy.yml
    } else {
        Write-Host "Install act to run workflows locally, then re-run with -RunAct." -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/6] Skipping local workflow simulation."
}

# [6/6] Docker Stack Build
Write-Host "[6/6] Verifying final Docker stack build (Silent)..."
if ($Verbose) {
    docker compose --env-file .env build
} else {
    docker compose --env-file .env build --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Final Docker build failed. Run with -Verbose for details." -ForegroundColor Red
    exit 1
}

Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Preflight complete. Local environment is healthy and secure.`n" -ForegroundColor Green
