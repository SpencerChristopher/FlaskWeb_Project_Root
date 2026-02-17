param(
    [switch]$RunAct
)

$ErrorActionPreference = "Stop"

function Require-Command($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Host "Missing required tool: $name"
        return $false
    }
    return $true
}

Write-Host "Preflight: GitHub Actions workflow lint"

if (Require-Command "actionlint") {
    actionlint -color -format '{{.Filepath}}:{{.Line}}:{{.Column}}: {{.Message}}' .github\workflows\*.yml
} else {
    Write-Host "Install actionlint via your package manager or from its release page, then re-run."
}

if ($RunAct) {
    Write-Host "Preflight: Local workflow run (act)"
    if (Require-Command "act") {
        act -W .github\workflows\test-deploy.yml
    } else {
        Write-Host "Install act to run workflows locally, then re-run with -RunAct."
    }
}
