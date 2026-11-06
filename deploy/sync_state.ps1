<#
.SYNOPSIS
    Synchronizes Forward Test State and Logs between Local PC and Google Cloud VM.
.DESCRIPTION
    Transfers logs/forward_test_state.json and logs/forward_test_footprint.jsonl
    so you can seamlessly move your live forward-test ledger between your local machine
    and the 24/7 Google Cloud VM without losing trade history or cumulative PnL.
.PARAMETER Direction
    "ToCloud" (Upload local state to VM) or "FromCloud" (Download VM state to local). Default: "ToCloud".
.PARAMETER VmHost
    IP address or SSH hostname of your Google Cloud VM.
.PARAMETER VmUser
    SSH username on the VM (default: "ubuntu").
.PARAMETER RemotePath
    Path to btc_swing_engine on the VM (default: "~/btc_swing_engine").
.EXAMPLE
    .\sync_state.ps1 -VmHost "34.122.45.67" -Direction "ToCloud"
    .\sync_state.ps1 -VmHost "34.122.45.67" -Direction "FromCloud"
#>
param (
    [string]$VmHost = "",
    [string]$VmUser = "ubuntu",
    [string]$Direction = "ToCloud",
    [string]$RemotePath = "~/btc_swing_engine"
)

if (-not $VmHost) {
    Write-Host "[ERROR] Please specify your Google Cloud VM External IP via -VmHost <IP>" -ForegroundColor Red
    Write-Host "Example: .\sync_state.ps1 -VmHost 34.122.45.67 -Direction ToCloud" -ForegroundColor Yellow
    exit 1
}

$localLogDir = Join-Path $PSScriptRoot "..\logs"
$stateFile = Join-Path $localLogDir "forward_test_state.json"
$footprintFile = Join-Path $localLogDir "forward_test_footprint.jsonl"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ">>> BTC SWING ENGINE - FORWARD TEST STATE SYNCHRONIZATION" -ForegroundColor Cyan
Write-Host ">>> VM Host:    $VmUser@$VmHost" -ForegroundColor White
Write-Host ">>> Direction:  $Direction" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

if ($Direction -eq "ToCloud") {
    Write-Host ">>> Uploading local forward test state to VM..." -ForegroundColor Green
    if (Test-Path $stateFile) {
        scp "$stateFile" "$VmUser@$VmHost`:$RemotePath/logs/"
        Write-Host "  [OK] Uploaded forward_test_state.json" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] forward_test_state.json not found locally." -ForegroundColor Yellow
    }

    if (Test-Path $footprintFile) {
        scp "$footprintFile" "$VmUser@$VmHost`:$RemotePath/logs/"
        Write-Host "  [OK] Uploaded forward_test_footprint.jsonl" -ForegroundColor Green
    } else {
        Write-Host "  [SKIP] forward_test_footprint.jsonl not found locally." -ForegroundColor Yellow
    }
} elseif ($Direction -eq "FromCloud") {
    Write-Host ">>> Downloading forward test state from VM to local..." -ForegroundColor Green
    if (-not (Test-Path $localLogDir)) {
        New-Item -ItemType Directory -Path $localLogDir -Force | Out-Null
    }
    scp "$VmUser@$VmHost`:$RemotePath/logs/forward_test_state.json" "$localLogDir/"
    scp "$VmUser@$VmHost`:$RemotePath/logs/forward_test_footprint.jsonl" "$localLogDir/"
    Write-Host "  [OK] Synced VM state to local logs/." -ForegroundColor Green
} else {
    Write-Host "[ERROR] Invalid direction: $Direction. Use 'ToCloud' or 'FromCloud'." -ForegroundColor Red
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ">>> SYNC COMPLETE." -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
