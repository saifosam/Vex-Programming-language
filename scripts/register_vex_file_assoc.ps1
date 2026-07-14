param(
    [switch]$MachineWide
)

$ErrorActionPreference = 'Stop'

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$iconPath = Join-Path $repoRoot 'assets\vex.ico'

if (-not (Test-Path $iconPath)) {
    throw "Icon file not found: $iconPath"
}

if ($MachineWide) {
    $identity = [Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
    $adminRole = [Security.Principal.WindowsBuiltInRole]::Administrator
    if (-not $identity.IsInRole($adminRole)) {
        throw 'Run this script as Administrator to install the icon machine-wide.'
    }
    $root = 'HKLM:\SOFTWARE\Classes'
}
else {
    $root = 'HKCU:\Software\Classes'
}

$ext = '.vex'
$progId = 'Vex.File'

New-Item -Path "$root\$ext" -Force | Out-Null
New-ItemProperty -Path "$root\$ext" -Name '(default)' -Value $progId -Force | Out-Null

New-Item -Path "$root\$progId" -Force | Out-Null
New-ItemProperty -Path "$root\$progId" -Name '(default)' -Value 'Vex File' -Force | Out-Null

New-Item -Path "$root\$progId\DefaultIcon" -Force | Out-Null
New-ItemProperty -Path "$root\$progId\DefaultIcon" -Name '(default)' -Value "$iconPath,0" -Force | Out-Null

if ($MachineWide) {
    Write-Host "Registered $ext for all users with icon $iconPath"
}
else {
    Write-Host "Registered $ext for the current user with icon $iconPath"
}
Write-Host 'Restart Explorer or sign out/in to refresh file icons.'
