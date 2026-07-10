$frontendPort = 5173
$existingFrontend = Get-NetTCPConnection -LocalPort $frontendPort -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingFrontend) {
    $ownerProcessId = $existingFrontend.OwningProcess
    Write-Host "Stopping existing process on port $frontendPort (PID: $ownerProcessId)"
    Stop-Process -Id $ownerProcessId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

Set-Location "$PSScriptRoot\frontend"
$env:PATH = "C:\Program Files\nodejs;" + $env:PATH
if (!(Test-Path "node_modules")) {
    & "C:\Program Files\nodejs\npm.cmd" install
}
Write-Host "Starting ProtoTree frontend from: $(Get-Location)"
& "C:\Program Files\nodejs\npm.cmd" run dev -- --host 127.0.0.1
