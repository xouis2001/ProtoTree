Set-Location $PSScriptRoot

$backendPort = 8001
$existingBackend = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingBackend) {
    $ownerProcessId = $existingBackend.OwningProcess
    Write-Host "Stopping existing process on port $backendPort (PID: $ownerProcessId)"
    Stop-Process -Id $ownerProcessId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $name = $parts[0].Trim()
            $value = $parts[1].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

if (!(Test-Path ".venv")) {
    python -m venv .venv
}

& ".\.venv\Scripts\python.exe" -m pip install -r ".\backend\requirements-local.txt"
Set-Location ".\backend"
Write-Host "Starting ProtoTree backend from: $(Get-Location)"
Write-Host "OpenAPI: http://127.0.0.1:$backendPort/openapi.json"
& "..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port $backendPort
