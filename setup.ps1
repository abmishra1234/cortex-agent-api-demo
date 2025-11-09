param([switch]$Install, [switch]$Run, [switch]$Test, [switch]$Clean, [switch]$Help)

if ($Help -or (-not ($Install -or $Run -or $Test -or $Clean))) {
    Write-Host 'Snowflake Cortex Agent - Setup Script' -ForegroundColor Yellow
    Write-Host 'Usage: .\setup.ps1 [options]'
    Write-Host 'Options: -Install, -Run, -Test, -Clean, -Help'
    exit 0
}

if ($Clean) {
    Write-Host 'Cleaning environment...' -ForegroundColor Cyan
    if (Test-Path venv) { Remove-Item -Recurse -Force venv }
    if (Test-Path .pytest_cache) { Remove-Item -Recurse -Force .pytest_cache }
    if (Test-Path htmlcov) { Remove-Item -Recurse -Force htmlcov }
    if (Test-Path .coverage) { Remove-Item -Force .coverage }
    Write-Host 'Done!' -ForegroundColor Green
}

if ($Install) {
    Write-Host 'Installing dependencies...' -ForegroundColor Cyan
    python -m venv venv
    & '.\venv\Scripts\Activate.ps1'
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    Write-Host 'Done!' -ForegroundColor Green
}

if ($Test) {
    Write-Host 'Running tests...' -ForegroundColor Cyan
    & '.\venv\Scripts\Activate.ps1'
    pytest --cov=. --cov-report=html --cov-report=term
    Write-Host 'Done!' -ForegroundColor Green
}

if ($Run) {
    Write-Host 'Starting application...' -ForegroundColor Cyan
    & '.\venv\Scripts\Activate.ps1'
    streamlit run streamlit.py
}
