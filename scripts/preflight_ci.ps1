param(
    [switch]$RunAct,
    [switch]$SmokeTest, # Run local CI-parity smoke test (no act required)
    [switch]$SkipAudit,
    [switch]$SkipCloud,
    [switch]$SkipRunner,
    [switch]$Offline,
    [switch]$Verbose,
    [switch]$StrictSecurity,
    [switch]$CheckArm # New: Explicitly check ARM64 build locally
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

function Get-PipAuditAllowlistArgs {
    $allowlistPath = Join-Path $PSScriptRoot "..\pip-audit-allowlist.txt"
    if (-not (Test-Path $allowlistPath)) { return "" }
    $entries = Get-Content $allowlistPath | ForEach-Object {
        $line = $_.Split('#')[0].Trim()
        if (-not [string]::IsNullOrWhiteSpace($line)) { $line }
    }
    if (-not $entries) { return "" }
    return " " + (($entries | ForEach-Object { "--ignore-vuln $_" }) -join " ")
}

function Read-DotEnv([string]$path) {
    $map = @{}
    if (-not (Test-Path $path)) { return $map }
    Get-Content $path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) { return }
        $parts = $line.Split("=", 2)
        if ($parts.Count -lt 2) { return }
        $key = $parts[0].Trim()
        if (-not $key) { return }
        $map[$key] = $parts[1]
    }
    return $map
}

$PipAuditAllowlistArgs = Get-PipAuditAllowlistArgs

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

# Local env alignment: .env (secrets) + .env.vars (non-secrets) should cover .env.template
$dotEnvPath = Join-Path $PSScriptRoot "..\.env"
$dotVarsPath = Join-Path $PSScriptRoot "..\.env.vars"
$dotTemplatePath = Join-Path $PSScriptRoot "..\.env.template"
$dotEnv = Read-DotEnv $dotEnvPath
$dotVars = Read-DotEnv $dotVarsPath
$dotTemplate = Read-DotEnv $dotTemplatePath

if ($dotTemplate.Count -gt 0) {
    $unknownInEnv = @($dotEnv.Keys | Where-Object { -not $dotTemplate.ContainsKey($_) })
    if ($unknownInEnv.Count -gt 0) {
        Write-Host "Warning: .env contains keys not in .env.template (new secrets?):" -ForegroundColor Yellow
        $unknownInEnv | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    }

    $unknownInVars = @($dotVars.Keys | Where-Object { -not $dotTemplate.ContainsKey($_) })
    if ($unknownInVars.Count -gt 0) {
        Write-Host "Warning: .env.vars contains keys not in .env.template:" -ForegroundColor Yellow
        $unknownInVars | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
    }

    $missing = @($dotTemplate.Keys | Where-Object { -not $dotEnv.ContainsKey($_) -and -not $dotVars.ContainsKey($_) })
    if ($missing.Count -gt 0) {
        Write-Host "Warning: Missing keys from both .env and .env.vars (local config incomplete):" -ForegroundColor Yellow
        $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
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

    # Check Secret Existence
    try {
        $remoteRepoSecrets = gh secret list | ForEach-Object { $_.Split("`t")[0] }
        $remoteStagingSecrets = gh secret list --env staging | ForEach-Object { $_.Split("`t")[0] }
        $remoteProdSecrets = gh secret list --env production | ForEach-Object { $_.Split("`t")[0] }

        $requiredRepoSecrets = @(
            "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD",
            "CONTACT_TO_EMAIL", "CONTACT_FROM_EMAIL", "PASSWORD_SERVICE_FROM_EMAIL",
            "TURNSTILE_SITE_KEY", "TURNSTILE_SECRET_KEY"
        )

        $requiredEnvSecrets = @(
            "SECRET_KEY", "ADMIN_USERNAME", "ADMIN_PASSWORD",
            "MONGO_ROOT_USER", "MONGO_ROOT_PASSWORD", "MONGO_APP_PASSWORD",
            "CLOUDFLARE_TUNNEL_TOKEN", "DOMAIN_NAME"
        )
        foreach ($s in $requiredRepoSecrets) {
            if ($s -notin $remoteRepoSecrets) {
                Write-Host "MISSING REPO SECRET: '$s' not found in GitHub." -ForegroundColor Red
                exit 1
            }
        }

        foreach ($s in $requiredEnvSecrets) {
            # Check if secret exists in environment OR variable exists in repository/environment
            if ($s -notin $remoteStagingSecrets -and $s -notin $allVarNames) {
                Write-Host "MISSING STAGING SECRET/VAR: '$s' not found in GitHub 'staging' environment or repository variables." -ForegroundColor Red
                exit 1
            }
            if ($s -notin $remoteProdSecrets -and $s -notin $allVarNames) {
                Write-Host "WARNING: Prod secret/var '$s' not found in GitHub 'production' environment or repository variables." -ForegroundColor Yellow
            }
        }
        Write-Host "GitHub Secrets: VERIFIED (Repo + Environments)" -ForegroundColor Green
    } catch {
        Write-Host "Warning: Could not fetch secret list." -ForegroundColor Yellow
    }

    # Validate that secrets/vars referenced in changed files exist in GitHub
    try {
        $repoVars = gh variable list --json name,value | ConvertFrom-Json
        $stagingVars = gh variable list --env staging --json name,value | ConvertFrom-Json
        $prodVars = gh variable list --env production --json name,value | ConvertFrom-Json

        $repoVarNames = @($repoVars | ForEach-Object { $_.name })
        $stagingVarNames = @($stagingVars | ForEach-Object { $_.name })
        $prodVarNames = @($prodVars | ForEach-Object { $_.name })
        $allVarNames = @($repoVarNames + $stagingVarNames + $prodVarNames | Sort-Object -Unique)

        $changedFiles = @()
        try {
            $base = git merge-base HEAD origin/dev 2>$null
            if ($base) {
                $changedFiles = git diff --name-only $base HEAD
            }
        } catch {
            $changedFiles = @()
        }
        if (-not $changedFiles -or $changedFiles.Count -eq 0) {
            $changedFiles = git status --porcelain | ForEach-Object {
                if ($_.Length -ge 4) { $_.Substring(3) } else { $null }
            }
        }
        $changedFiles = $changedFiles | Where-Object { $_ -and (Test-Path $_) }
        $workflowFiles = $changedFiles | Where-Object { $_ -match '^\.github[\\/].*\.(yml|yaml)$' }

        $secretRefs = New-Object System.Collections.Generic.HashSet[string]
        $varRefs = New-Object System.Collections.Generic.HashSet[string]

        foreach ($file in $workflowFiles) {
            try {
                $content = Get-Content -Raw -Path $file
            } catch {
                continue
            }

            foreach ($m in [regex]::Matches($content, 'secrets\.(\w+)', 'IgnoreCase')) {
                [void]$secretRefs.Add($m.Groups[1].Value)
            }
            foreach ($m in [regex]::Matches($content, 'secrets\[[''"]([^''"]+)[''"]\]', 'IgnoreCase')) {
                [void]$secretRefs.Add($m.Groups[1].Value)
            }

            foreach ($m in [regex]::Matches($content, 'vars\.(\w+)', 'IgnoreCase')) {
                [void]$varRefs.Add($m.Groups[1].Value)
            }
            foreach ($m in [regex]::Matches($content, 'vars\[[''"]([^''"]+)[''"]\]', 'IgnoreCase')) {
                [void]$varRefs.Add($m.Groups[1].Value)
            }
        }

        if ($secretRefs.Count -gt 0 -and $workflowFiles.Count -gt 0) {
            $missingSecrets = @()
            foreach ($s in $secretRefs) {
                if ($s -eq "GITHUB_TOKEN") { continue }
                if ($s -notin $remoteRepoSecrets -and $s -notin $remoteStagingSecrets -and $s -notin $remoteProdSecrets) {
                    $missingSecrets += $s
                }
            }
            if ($missingSecrets.Count -gt 0) {
                Write-Host "Warning: Secrets referenced in changed files missing from GitHub (repo + env):" -ForegroundColor Yellow
                $missingSecrets | Sort-Object -Unique | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
            }
        }

        if ($varRefs.Count -gt 0 -and $workflowFiles.Count -gt 0) {
            $missingVars = @()
            foreach ($v in $varRefs) {
                if ($v -notin $allVarNames) {
                    $missingVars += $v
                }
            }
            if ($missingVars.Count -gt 0) {
                Write-Host "Warning: Vars referenced in changed files missing from GitHub (repo + env):" -ForegroundColor Yellow
                $missingVars | Sort-Object -Unique | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
            }
        }

        if ($dotVars.Count -gt 0 -and $allVarNames.Count -gt 0) {
            $localOnlyVars = @($dotVars.Keys | Where-Object { $_ -notin $allVarNames })
            if ($localOnlyVars.Count -gt 0) {
                Write-Host "Warning: .env.vars contains keys not present in GitHub variables (repo + env):" -ForegroundColor Yellow
                $localOnlyVars | Sort-Object -Unique | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
            }
        }

        if ($dotEnv.Count -gt 0) {
            $localOnlySecrets = @($dotEnv.Keys | Where-Object { $_ -notin $dotVars.Keys -and $_ -notin $remoteRepoSecrets -and $_ -notin $remoteStagingSecrets -and $_ -notin $remoteProdSecrets })
            if ($localOnlySecrets.Count -gt 0) {
                Write-Host "Warning: .env contains secrets not present in GitHub (repo + env):" -ForegroundColor Yellow
                $localOnlySecrets | Sort-Object -Unique | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
            }
        }
    } catch {
        Write-Host "Warning: Could not validate secrets/vars referenced in changed files." -ForegroundColor Yellow
    }
}

# [3/8] Containerized Validation (Lint & Audit)
Write-Host "[3/8] Running containerized lints and security audits..."
if ($SkipAudit) {
    Write-Host "Skipping validation as requested." -ForegroundColor Yellow
} else {
    Write-Host "Running pip-audit and bandit..."
    docker run --rm -e PIP_DISABLE_PIP_VERSION_CHECK=1 -v "${PWD}:/app" -w /app python:3.12-slim-bookworm /bin/sh -c "pip install --quiet --root-user-action=ignore poetry==2.0.1 poetry-plugin-export==1.9.0 pip-audit==2.8.0 bandit==1.8.2 && poetry export --format=constraints.txt --output=constraints.txt --without-hashes && pip-audit -r constraints.txt$PipAuditAllowlistArgs && bandit -r src/ -ll && rm constraints.txt"
    
    Write-Host "Running actionlint (All Workflows)..."
    # Resolve file paths explicitly so they are passed to the container correctly
    $workflowFiles = Get-ChildItem -Path ".github/workflows/*.yml" | ForEach-Object { ".github/workflows/$($_.Name)" }
    if ($workflowFiles.Count -gt 0) {
        docker run --rm -v "${PWD}:/app" -w /app rhysd/actionlint:latest -config-file .github/actionlint.yaml $workflowFiles
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: Workflow linting failed." -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Warning: No workflow files found to lint." -ForegroundColor Yellow
    }
    
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

# [6/8] CI Parity Smoke Test
if ($SmokeTest) {
    Write-Host "[6/8] Running CI-Parity Smoke Test (Up -> Seed -> Test)..."
    $prevTurnstileEnabled = $env:TURNSTILE_ENABLED
    $prevTurnstileLoginEnabled = $env:TURNSTILE_LOGIN_ENABLED
    $env:TURNSTILE_ENABLED = "false"
    $env:TURNSTILE_LOGIN_ENABLED = "false"
    try {
        Write-Host "Resetting stack..."
        docker compose --env-file .env --env-file .env.vars -f docker-compose.yml -f docker-compose.ci.yml down --remove-orphans
        
        Write-Host "Building & Starting CI stack..."
        $env:IMAGE_TAG = "preflight-local"
        docker compose --env-file .env --env-file .env.vars -f docker-compose.yml -f docker-compose.ci.yml up -d --build --wait --wait-timeout 180
        
        Write-Host "Verifying container health (localhost:5005)..."
        curl.exe -f --retry 12 --retry-delay 5 --retry-connrefused http://localhost:5005/ | Out-Null
        curl.exe -f --retry 8 --retry-delay 3 http://localhost:5005/api/home | Out-Null

        Write-Host "Asserting web container health..."
        $healthStatus = docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' flask_web_app
        if ($healthStatus -ne "healthy") {
            Write-Host "flask_web_app did not reach healthy state." -ForegroundColor Red
            docker logs --tail 200 flask_web_app
            exit 1
        }
        
        Write-Host "Seeding..."
        docker exec flask_web_app /app/.venv/bin/python scripts/seed_db.py
        
        Write-Host "Injecting tests (CI Parity)..."
        docker exec flask_web_app /bin/sh -c "mkdir -p /app/tests"
        docker cp tests/. flask_web_app:/app/tests
        docker cp pytest.ini flask_web_app:/app/pytest.ini

        Write-Host "Running containerized tests (including prod readiness)..."
        docker exec -e PYTHONPATH=/app flask_web_app /app/.venv/bin/pytest /app/tests -m "not e2e and not performance and not smoke and not heavy"
        if ($LASTEXITCODE -ne 0) {
            throw "CI-parity tests failed."
        }
        
        Write-Host "Smoke and functional tests PASSED." -ForegroundColor Green
    } catch {
        Write-Host "Tests FAILED." -ForegroundColor Red
        exit 1
    } finally {
        docker compose --env-file .env --env-file .env.vars -f docker-compose.yml -f docker-compose.ci.yml down
        if ($null -ne $prevTurnstileEnabled) { $env:TURNSTILE_ENABLED = $prevTurnstileEnabled } else { Remove-Item Env:TURNSTILE_ENABLED -ErrorAction SilentlyContinue }
        if ($null -ne $prevTurnstileLoginEnabled) { $env:TURNSTILE_LOGIN_ENABLED = $prevTurnstileLoginEnabled } else { Remove-Item Env:TURNSTILE_LOGIN_ENABLED -ErrorAction SilentlyContinue }
    }
} else {
    Write-Host "[6/8] Skipping CI-Parity Smoke Test." -ForegroundColor Gray
}

# [7/8] Docker Stack & ARM64 Validation
Write-Host "[7/8] Validating Docker configurations..."

# Lint Dockerfile
Write-Host "Linting Dockerfile (hadolint)..."
if (Require-Command "docker") {
    Get-Content Dockerfile | docker run --rm -i hadolint/hadolint
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Dockerfile linting failed." -ForegroundColor Red
        exit 1
    }
}

# Validate Compose Stack (Full Staging Parity)
Write-Host "Validating Compose Configuration (Staging Parity)..."
$env:IMAGE_TAG = "preflight-local"
# Include all staging-relevant files to ensure they merge correctly
docker compose --env-file .env --env-file .env.vars -f docker-compose.yml -f docker-compose.ci.yml -f docker-compose.staging.yml config -q
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Docker Compose configuration is invalid or files do not merge correctly." -ForegroundColor Red
    exit 1
}

if ($CheckArm) {
    Write-Host "Verifying ARM64 Build compatibility..."
    docker buildx build --platform linux/arm64 --build-arg PYTHON_IMAGE=python:3.12-slim-bookworm@sha256:4c50375fc4b8ea5ca06ac9485186ccb50171c99390b0e9300c2bac871cc2dc3e . --tag arm64-preflight --load=false
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: ARM64 Build failed." -ForegroundColor Red
        exit 1
    }
}

# [8/8] Infrastructure CVE Baseline Audit
Write-Host "[8/8] Auditing Infrastructure CVE Baseline (Docker Scout)..."
$images = @(
    "nginx:stable-alpine-slim@sha256:c9d648d0547ebfe3cbd197c73f5a8b5a8bdf4e215c76d290f93952e1a7154891",
    "mongo:8.0.19-noble@sha256:1773d7826e340cd966f439a4e71abea42fd9ca70ddce1ab6b96eb76013c3ca8e",
    "redis:7.4-alpine@sha256:8b81dd37ff027bec4e516d41acfbe9fe2460070dc6d4a4570a2ac5b9d59df065"
)
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
