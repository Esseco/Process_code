[CmdletBinding()]
param([int]$Port = 0)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $root 'search_tool_server.ps1'
$windowsPowerShell = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
if (-not (Test-Path -LiteralPath $windowsPowerShell)) { $windowsPowerShell = 'powershell.exe' }
$stdoutLog = Join-Path $root 'search_tool_server.out.log'
$stderrLog = Join-Path $root 'search_tool_server.err.log'

function Test-Service([string]$Url) {
    try {
        $request = [System.Net.WebRequest]::Create("$Url/api/health")
        $request.Proxy = $null
        $request.Timeout = 1000
        $response = $request.GetResponse()
        try { return ([int]$response.StatusCode -eq 200) } finally { $response.Close() }
    } catch { return $false }
}

function Open-Browser([string]$Url) {
    try { Start-Process -FilePath "$Url/" } catch { Write-Host "Open this address manually: $Url/" }
}

$candidates = if ($Port -gt 0) { @($Port) } else { @(29990..30020) }
foreach ($candidate in $candidates) {
    $url = "http://127.0.0.1:$candidate"
    if (Test-Service $url) { Open-Browser $url; exit 0 }
    Remove-Item -LiteralPath $stdoutLog,$stderrLog -Force -ErrorAction SilentlyContinue
    try {
        $process = Start-Process -FilePath $windowsPowerShell -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',$server,'-Port',$candidate) -WorkingDirectory $root -WindowStyle Minimized -PassThru -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
    } catch { continue }
    for ($i = 0; $i -lt 30 -and -not (Test-Service $url); $i++) { Start-Sleep -Milliseconds 250 }
    if ((Test-Service $url) -or ($process -and -not $process.HasExited)) {
        Open-Browser $url
        exit 0
    }
}

Write-Host 'Search service failed to start on ports 29990-30020.'
if (Test-Path -LiteralPath $stderrLog) { Get-Content -LiteralPath $stderrLog -Tail 20 }
exit 1

