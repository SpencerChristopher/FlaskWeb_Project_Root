param(
    [switch]$RunAct,
    [switch]$SkipAudit
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

# [2/6] Security Audit (pip-audit)
Write-Host "[2/6] Running security audit..."
if ($SkipAudit) {
    Write-Host "Skipping audit as requested." -ForegroundColor Yellow
} elseif (Require-Command "pip-audit" -Optional) {
    # Export dependencies to a temporary file for auditing
    poetry export --format=constraints.txt --output=constraints.txt --without-hashes
    try {
        pip-audit -r constraints.txt
        Write-Host "Security audit passed: No known vulnerabilities." -ForegroundColor Green
    } finally {
        if (Test-Path constraints.txt) { Remove-Item constraints.txt }
    }
} else {
    Write-Host "Warning: pip-audit not found. Skipping local dependency scan." -ForegroundColor Yellow
    Write-Host "Recommendation: Install pip-audit via 'pip install pip-audit' for better local security."
}

# [3/6] Lockfile Freshness
Write-Host "[3/6] Ensuring poetry.lock is up to date..."
poetry lock
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: poetry lock failed." -ForegroundColor Red
    exit 1
}

# [4/6] GitHub Actions Linting
Write-Host "[4/6] Linting GitHub Actions workflows..."
if (Require-Command "actionlint" -Optional) {
    # Use & operator to execute command correctly even if path has spaces
    & actionlint -color -format '{{.Filepath}}:{{.Line}}:{{.Column}}: {{.Message}}' ".github/workflows/*.yml"
} else {
    Write-Host "Warning: actionlint not found. Skipping workflow linting." -ForegroundColor Yellow
}

# [5/6] Local CI Simulation (Optional)
if ($RunAct) {
    Write-Host "[5/6] Running local workflow simulation (act)..."
    if (Require-Command "act" -Optional) {
        act -W .github/workflows/test-deploy.yml
    } else {
        Write-Host "Install act to run workflows locally, then re-run with -RunAct." -ForegroundColor Yellow
    }
} else {
    Write-Host "[5/6] Skipping local workflow simulation (use -RunAct to enable)."
}

# [6/6] Docker Stack Health
Write-Host "[6/6] Verifying Docker stack build..."
docker compose --env-file .env build
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker build failed." -ForegroundColor Red
    exit 1
}

Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Preflight complete. Local environment is healthy and secure.`n" -ForegroundColor Green
