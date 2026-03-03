param(
    [switch]$RunAct,
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

# [1/7] Tool Check
Write-Host "[1/7] Verifying required tools..."
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

# [2/7] Cloud State Validation (GitHub CLI)
# ... (rest of the cloud state logic remains unchanged)
if (-not $SkipCloud -and -not $Offline) {
    Write-Host "[2/7] Validating Cloud State (GitHub)..."
    
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

    # Check Dependabot Alerts
    try {
        $alerts = gh api repos/:owner/:repo/dependabot/alerts -f state=open | ConvertFrom-Json
        if ($alerts.Count -gt 0) {
            Write-Host "CRITICAL: GitHub has detected $($alerts.Count) OPEN Dependabot vulnerabilities." -ForegroundColor Red
            foreach ($a in $alerts) {
                Write-Host " - [$($a.security_advisory.severity)] $($a.security_advisory.summary)" -ForegroundColor Yellow
            }
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
    Write-Host "[2/7] Skipping Cloud State Validation (Offline Mode)." -ForegroundColor Yellow
}

# [3/7] Containerized Validation (Lint & Audit)
Write-Host "[3/7] Running containerized lints and security audits..."
if ($SkipAudit) {
    Write-Host "Skipping validation as requested." -ForegroundColor Yellow
} else {
    Write-Host "Running pip-audit and bandit..."
    docker run --rm -v "${PWD}:/app" -w /app python:3.11-slim-bookworm /bin/sh -c "pip install --quiet poetry poetry-plugin-export pip-audit bandit && poetry export --format=constraints.txt --output=constraints.txt --without-hashes && pip-audit -r constraints.txt && bandit -r src/ -ll && rm constraints.txt"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Security audit failed." -ForegroundColor Red
        exit 1
    }

    Write-Host "Running actionlint..."
    docker run --rm -v "${PWD}:/app" -w /app rhysd/actionlint:latest -config-file .github/actionlint.yaml .github/workflows/test-deploy.yml .github/workflows/production-deploy.yml
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Workflow linting failed." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Validation passed." -ForegroundColor Green
}

# [4/7] Lockfile Freshness
Write-Host "[4/7] Ensuring poetry.lock is up to date..."
poetry lock --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: poetry lock failed." -ForegroundColor Red
    exit 1
}

# [5/7] Local CI Simulation (Optional)
if ($RunAct) {
    Write-Host "[5/7] Running local workflow simulation (act)..."
    if (Require-Command "act" -Optional) {
        & act -W .github/workflows/test-deploy.yml
    } else {
        Write-Host "Install act to run workflows locally, then re-run with -RunAct." -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/7] Skipping local workflow simulation."
}

# [6/7] Docker Stack Build
Write-Host "[6/7] Verifying final Docker stack build..."
if ($Verbose) {
    docker compose build
} else {
    docker compose build --quiet
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Final Docker build failed." -ForegroundColor Red
    exit 1
}

# [7/7] Infrastructure CVE Baseline Audit (Docker Scout)
Write-Host "[7/7] Auditing Infrastructure CVE Baseline (Docker Scout)..."
$images = @("nginx:alpine", "mongo:8.0", "redis:alpine")

# Try to check if docker scout is available
if (Require-Command "docker" -and (docker scout version 2>&1 | Out-String -ErrorAction SilentlyContinue)) {
    foreach ($img in $images) {
        Write-Host "Auditing $img..." -NoNewline
        if ($StrictSecurity) {
            # In Strict mode, we fail on any High/Critical CVEs using 'cves' which supports --exit-code and --only-severity
            docker scout cves $img --exit-code --only-severity critical,high
            if ($LASTEXITCODE -ne 0) {
                Write-Host " [FAILED]" -ForegroundColor Red

                Write-Host "Error: $img contains High/Critical vulnerabilities. Resolve them or run without -StrictSecurity." -ForegroundColor Red
                exit 1
            }
            Write-Host " [CLEAN]" -ForegroundColor Green
        } else {
            # In Normal mode, we just print the summary for visibility
            docker scout quickview $img
        }
    }
} else {
    Write-Host "Warning: Docker Scout not found. Skipping infrastructure audit." -ForegroundColor Yellow
    Write-Host "Install Docker Scout for baseline CVE monitoring." -ForegroundColor Gray
}

Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Preflight complete. Local environment is healthy and secure.`n" -ForegroundColor Green
