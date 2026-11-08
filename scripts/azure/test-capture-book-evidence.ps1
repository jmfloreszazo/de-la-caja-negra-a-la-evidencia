#requires -Version 7.4
$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('book-capture-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $root | Out-Null
$script:calls = @()
$script:fail = $false
function az {
    $script:calls += ,@($args)
    if ($script:fail) { $global:LASTEXITCODE = 17; Write-Output '{"error":"synthetic"}'; return }
    $global:LASTEXITCODE = 0
    Write-Output '{"synthetic":true}'
}
function Invoke-Capture([string]$Path) {
    . "$PSScriptRoot\capture-book-evidence.ps1" -SubscriptionId '00000000-0000-0000-0000-000000000001' `
        -ResourceGroup fixture -RunnerName fixture-runner -WorkerScaleSetName fixture-workers `
        -StorageAccountName fixturestorage -OutputDirectory $Path
}
try {
    $output = Join-Path $root 'good'
    Invoke-Capture $output
    $record = Get-Content (Join-Path $output 'capture.json') -Raw | ConvertFrom-Json
    if ($record.status -ne 'PASS' -or $record.commands.Count -ne 6) { throw 'Incomplete capture' }
    foreach ($call in $script:calls) {
        if ($call -notcontains '--subscription' -or $call -contains 'create' -or $call -contains 'keys') { throw 'Unexpected operation' }
    }
    $rejected = $false
    try { Invoke-Capture $output } catch { $rejected = $_.Exception.Message -like '*new capture directory*' }
    if (-not $rejected -or $script:calls.Count -ne 6) { throw 'Existing capture was not protected' }
    $script:fail = $true
    $bad = Join-Path $root 'bad'
    $rejected = $false
    try { Invoke-Capture $bad } catch { $rejected = $_.Exception.Message -like '*capture failed*' }
    $record = Get-Content (Join-Path $bad 'capture.json') -Raw | ConvertFrom-Json
    if (-not $rejected -or $record.status -ne 'FAIL' -or $record.commands[0].exitCode -ne 17) { throw 'Failure evidence lost' }
    $global:LASTEXITCODE = 0
    Write-Output 'BOOK CLI CAPTURE TESTS: PASS (read-only, explicit subscription, no overwrite, retained failure)'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force
}
