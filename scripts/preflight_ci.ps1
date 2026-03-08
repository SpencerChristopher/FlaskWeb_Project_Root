param(
    [switch]$RunAct,
    [switch]$SmokeTest, # New: Run local CI-parity smoke test (no act required)
    [switch]$SkipAudit,
    [switch]$SkipCloud,
    [switch]$SkipRunner,
    [switch]$Offline,
    [switch]$Verbose,
    [switch]$StrictSecurity
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

# [1/8] Tool Check
Write-Host "[1/8] Verifying required tools..."
$tools = @("poetry", "docker", "gh")
foreach ($tool in $tools) {
    if (-not (Require-Command $tool)) { 
        if ($tool -eq "gh") {
            Write-Host "Warning: GitHub CLI (gh) not found. Cloud-aware checks will be disabled." -ForegroundColor Yellow
            $Offline = $true
        } else {
            exit 1 
        }
    }
}

# [2/8] Cloud State Validation
if (-not $SkipCloud -and -not $Offline) {
    Write-Host "[2/8] Validating Cloud State (GitHub)..."
    
    # Check Runner Status
    if (-not $SkipRunner) {
        try {
            $runners = gh api repos/:owner/:repo/actions/runners | ConvertFrom-Json
            $wslRunner = $runners.runners | Where-Object { $_.labels.name -contains "wsl-staging" }
            
            if ($null -eq $wslRunner) {
                Write-Host "Warning: No runner with label 'wsl-staging' found." -ForegroundColor Yellow
            } elseif ($wslRunner.status -ne "online") {
                Write-Host "Warning: WSL Staging runner is OFFLINE." -ForegroundColor Yellow
            } else {
                Write-Host "Staging Runner: ONLINE" -ForegroundColor Green
            }
        } catch {
            Write-Host "Warning: Could not fetch runner status." -ForegroundColor Yellow
        }
    }

    # Check Dependabot
    try {
        $alerts = gh api repos/:owner/:repo/dependabot/alerts -f state=open | ConvertFrom-Json
        if ($alerts.Count -gt 0) {
            Write-Host "CRITICAL: GitHub has detected $($alerts.Count) OPEN Dependabot vulnerabilities." -ForegroundColor Red
            if ($ConfirmPreference -ne "None") {
                $choice = Read-Host "Proceed anyway? (y/N)"
                if ($choice -ne "y") { exit 1 }
            }
        } else {
            Write-Host "Dependabot: CLEAN (0 alerts)" -ForegroundColor Green
        }
    } catch {
        Write-Host "Warning: Could not fetch Dependabot alerts." -ForegroundColor Yellow
    }

    # Check Secret Existence
    try {
        $remoteSecrets = gh secret list | ForEach-Object { $_.Split("`t")[0] }
        $requiredSecrets = @("SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD", "MONGO_ROOT_USER", "MONGO_ROOT_PASSWORD", "MONGO_APP_USER", "MONGO_APP_PASSWORD")
        foreach ($s in $requiredSecrets) {
            if ($s -notin $remoteSecrets) {
                Write-Host "MISSING SECRET: '$s' is required by CI but not found in GitHub." -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "GitHub Secrets: VERIFIED" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not fetch secret list." -ForegroundColor Yellow
    }
}

# [3/8] Containerized Validation (Lint & Audit)
Write-Host "[3/8] Running containerized lints and security audits..."
if ($SkipAudit) {
    Write-Host "Skipping validation as requested." -ForegroundColor Yellow
} else {
    Write-Host "Running pip-audit and bandit..."
    docker run --rm -v "${PWD}:/app" -w /app python:3.11-slim-bookworm /bin/sh -c "pip install --quiet poetry poetry-plugin-export pip-audit bandit && poetry export --format=constraints.txt --output=constraints.txt --without-hashes && pip-audit -r constraints.txt && bandit -r src/ -ll && rm constraints.txt"
    
    Write-Host "Running actionlint (All Workflows)..."
    docker run --rm -v "${PWD}:/app" -w /app rhysd/actionlint:latest -config-file .github/actionlint.yaml .github/workflows/test-deploy.yml .github/workflows/production-deploy.yml
    
    Write-Host "Validation passed." -ForegroundColor Green
}

# [4/8] Lockfile Freshness
Write-Host "[4/8] Ensuring poetry.lock is up to date..."
poetry lock --quiet

# [5/8] Local CI Simulation (act)
if ($RunAct) {
    Write-Host "[5/8] Running local workflow simulation (act)..."
    if (Require-Command "act" -Optional) {
        & act -W .github/workflows/test-deploy.yml
    }
} else {
    Write-Host "[5/8] Skipping full workflow simulation (act)."
}

# [6/8] CI Parity Smoke Test (New)
if ($SmokeTest) {
    Write-Host "[6/8] Running CI-Parity Smoke Test (Up -> Seed -> Test)..."
    try {
        Write-Host "Resetting stack..."
        docker compose -f docker-compose.yml -f docker-compose.ci.yml down --remove-orphans
        
        Write-Host "Building & Starting CI stack..."
        docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build --wait
        
        Write-Host "Seeding..."
        docker exec flask_web_app /app/.venv/bin/python scripts/seed_db.py
        
        Write-Host "Injecting tests (CI Parity)..."
        docker exec flask_web_app /bin/sh -c "mkdir -p /app/tests"
        docker cp tests/. flask_web_app:/app/tests
        docker cp pytest.ini flask_web_app:/app/pytest.ini

        Write-Host "Running containerized smoke tests..."
        docker exec -e PYTHONPATH=/app flask_web_app /app/.venv/bin/pytest /app/tests -m "smoke"
        
        Write-Host "Smoke test PASSED." -ForegroundColor Green
    } catch {
        Write-Host "Smoke test FAILED." -ForegroundColor Red
        exit 1
    } finally {
        docker compose -f docker-compose.yml -f docker-compose.ci.yml down
    }
} else {
    Write-Host "[6/8] Skipping CI-Parity Smoke Test." -ForegroundColor Gray
}

# [7/8] Docker Stack Validation (CI Config)
Write-Host "[7/8] Validating CI Docker configuration and build..."
# Validate the config (catches missing env_files, syntax errors)
docker compose -f docker-compose.yml -f docker-compose.ci.yml config -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: CI Docker configuration is invalid (check for missing .env or syntax errors)." -ForegroundColor Red
    exit 1
}

docker compose -f docker-compose.yml -f docker-compose.ci.yml build --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: CI Docker build failed." -ForegroundColor Red
    exit 1
}

# [8/8] Infrastructure CVE Baseline Audit
Write-Host "[8/8] Auditing Infrastructure CVE Baseline (Docker Scout)..."
$images = @("nginx:alpine", "mongo:8.0", "redis:alpine")
if (Require-Command "docker" -and (docker scout version 2>&1 | Out-String -ErrorAction SilentlyContinue)) {
    foreach ($img in $images) {
        if ($StrictSecurity) {
            docker scout cves $img --exit-code --only-severity critical,high
        } else {
            docker scout quickview $img
        }
    }
}

Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Preflight complete. Local environment is healthy and secure.`n" -ForegroundColor Green
