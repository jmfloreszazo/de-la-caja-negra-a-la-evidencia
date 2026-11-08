#requires -Version 7.4
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\lab.ps1"
$checks = 0
function Assert([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
    $script:checks++
}
function Assert-Fails([scriptblock]$Operation, [string]$Pattern) {
    $message = ''
    try { & $Operation } catch { $message = $_.Exception.Message }
    Assert ($message -match $Pattern) "Expected failure matching '$Pattern', got '$message'"
}

$fixture = Join-Path ([IO.Path]::GetTempPath()) ("azure-lab-test-" + [guid]::NewGuid().ToString('N'))
$parameterPath = Join-Path $fixture 'parameters.json'
New-Item -ItemType Directory -Path $fixture | Out-Null
try {
    $OutputDirectory = $fixture
    function az {
        $script:capturedArguments = @($args)
        $global:LASTEXITCODE = 0
        '{"status":"Succeeded","changes":[]}'
    }
    $preview = Invoke-Azure @('deployment', 'group', 'what-if', '--resource-group', 'test-lab')
    Assert ($preview.status -eq 'Succeeded') 'WhatIf JSON must be parsed'
    Assert ($capturedArguments -contains '--no-pretty-print') 'WhatIf must disable human-readable output before JSON parsing'
    [void](Invoke-Azure @('group', 'show', '--name', 'test-lab'))
    Assert ($capturedArguments -notcontains '--no-pretty-print') 'WhatIf-only flags must not reach other Azure commands'
    Remove-Item Function:\az
    foreach ($n in @(0, 1, 2, 4, 8, 16)) {
        Assert-ScaleChange 0 $n $false
        $checks++
    }
    Assert-Fails { Assert-ScaleChange 1 3 $false } 'Capacity must'
    Assert-Fails { Assert-ScaleChange 4 2 $false } 'Scale-in deletes'
    Assert-ScaleChange 4 2 $true
    $checks++
    Assert-RunResult ([pscustomobject]@{ value = @([pscustomobject]@{ message = "log`nAZURE_LAB_EXIT=0`n" }) })
    $checks++
    Assert-Fails { Assert-RunResult ([pscustomobject]@{ value = @([pscustomobject]@{ message = 'Provisioning succeeded' }) }) } 'completion marker'
    Assert-Fails { Assert-RunResult ([pscustomobject]@{ value = @([pscustomobject]@{ message = 'AZURE_LAB_EXIT=7' }) }) } 'Guest execution failed'
    Assert-Fails { Assert-RunResult ([pscustomobject]@{ value = @([pscustomobject]@{ message = "AZURE_LAB_EXIT=0`nAZURE_LAB_EXIT=0" }) }) } 'Guest execution failed'
    Assert-Fails { Assert-LabParameters (Join-Path $Root 'infra\experiments\example.parameters.json') } 'placeholder'
    $parameters = @{
        parameters = @{
            prefix = @{ value = 'booklab' }
            sshPublicKey = @{ value = 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFixtureForValidationOnly' }
            expiresOn = @{ value = [datetime]::UtcNow.AddDays(2).ToString('yyyy-MM-dd') }
            monthlyBudgetAmount = @{ value = 100 }
            budgetEmail = @{ value = 'operator@example.com' }
            enableManagedPostgres = @{ value = $false }
        }
    }
    Save-Json $parameters $parameterPath
    $valid = Assert-LabParameters $parameterPath
    Assert ($valid.prefix.value -eq 'booklab') 'Valid parameters were not accepted'
    $parameters.parameters.expiresOn.value = '2000-01-01'
    Save-Json $parameters $parameterPath
    Assert-Fails { Assert-LabParameters $parameterPath } 'future review date'

    $script:azureCalls = 0
    function Invoke-Azure([string[]]$Arguments) {
        $script:azureCalls++
        throw 'An unexpected Azure operation was attempted by an offline test.'
    }
    $SubscriptionId = '00000000-0000-0000-0000-000000000001'
    $ResourceGroup = 'test-lab'
    $Apply = [System.Management.Automation.SwitchParameter]$false
    foreach ($operation in @('Deploy', 'Scale', 'Start', 'Deallocate', 'Run')) {
        $Action = $operation
        Assert-Fails { Invoke-LabAction } 'rerun explicitly with -Apply'
    }
    $Action = 'WhatIf'
    $ParametersFile = Join-Path $Root 'infra\experiments\example.parameters.json'
    Assert-Fails { Invoke-LabAction } 'placeholder'
    Assert ($azureCalls -eq 0) 'Guards must fail before contacting Azure'
    $Action = 'Run'
    $Experiment = 'e1-sqlserver'
    $Apply = [System.Management.Automation.SwitchParameter]$true
    Assert-Fails { Invoke-LabAction } 'AcceptSqlServerLicense'
    $AcceptSqlServerLicense = [System.Management.Automation.SwitchParameter]$true
    $SqlServerImage = 'untrusted.invalid/sql:2022'
    Assert-Fails { Invoke-LabAction } 'official SQL Server 2022'
    Assert ($azureCalls -eq 0) 'SQL Server consent and image guards must fail before contacting Azure'
    $Experiment = 'e4-replay'
    Assert-Fails { Invoke-LabAction } 'E4AttemptDirectory'
    Assert ($azureCalls -eq 0) 'Missing E4 inputs must fail before contacting Azure'
    $Experiment = 'core'
    $E4AttemptDirectory = 'unexpected-inputs'
    Assert-Fails { Invoke-LabAction } 'only be supplied for e4-replay'
    $E4AttemptDirectory = ''
    $AcceptSqlServerLicense = [System.Management.Automation.SwitchParameter]$false
    $SqlServerImage = 'mcr.microsoft.com/mssql/server:2022-latest'

    function Invoke-Azure([string[]]$Arguments) {
        switch ($Arguments[0..1] -join ' ') {
            'group exists' { return $true }
            'group show' { return [pscustomobject]@{ tags = [pscustomobject]@{ purpose = 'book-experiments' } } }
            'vmss list' { return [pscustomobject]@{ name = 'booklab-workers'; sku = [pscustomobject]@{ capacity = 4 } } }
            default { throw "Unexpected mutating operation: $($Arguments -join ' ')" }
        }
    }
    $parameters.parameters.expiresOn.value = [datetime]::UtcNow.AddDays(2).ToString('yyyy-MM-dd')
    Save-Json $parameters $parameterPath
    $ParametersFile = $parameterPath
    $Action = 'Deploy'
    $Apply = [System.Management.Automation.SwitchParameter]$true
    Assert-Fails { Invoke-LabAction } 'Scale-in deletes'

    $armPath = Join-Path $Root 'lab\results\azure\main.json'
    if (-not (Test-Path -LiteralPath $armPath)) { throw 'Run lab.ps1 -Action Build before these tests.' }
    $arm = Get-Content -LiteralPath $armPath -Raw | ConvertFrom-Json -Depth 100
    $storage = @($arm.resources | Where-Object type -eq 'Microsoft.Storage/storageAccounts')[0]
    Assert (-not $storage.properties.allowSharedKeyAccess) 'Storage must refuse shared keys'
    Assert (-not $storage.properties.allowBlobPublicAccess) 'Storage must refuse anonymous blobs'
    $vm = @($arm.resources | Where-Object type -eq 'Microsoft.Compute/virtualMachines')[0]
    Assert $vm.properties.osProfile.linuxConfiguration.disablePasswordAuthentication 'VM must refuse password SSH'
    Assert ($arm.parameters.workerCount.defaultValue -eq 0) 'No worker VMs should be created by default'
    Assert (-not $arm.parameters.enableManagedPostgres.defaultValue) 'Managed database costs must be opt-in'
    Assert (@($arm.resources | Where-Object type -eq 'Microsoft.Insights/autoscaleSettings').Count -eq 0) 'Autoscale must not change fixed experimental replica counts'
    $module = @($arm.resources | Where-Object type -eq 'Microsoft.Resources/deployments')[0]
    $database = @($module.properties.template.resources | Where-Object type -eq 'Microsoft.DBforPostgreSQL/flexibleServers')[0]
    Assert ($database.properties.authConfig.passwordAuth -eq 'Disabled') 'Managed PostgreSQL must be Entra-only'
    Assert ($database.properties.network.publicNetworkAccess -eq 'Disabled') 'Managed PostgreSQL must remain private'
    Write-Output "AZURE LAB OFFLINE CHECKS: PASS ($checks checks; no Azure calls)"
} finally {
    if (Test-Path -LiteralPath $parameterPath) { Remove-Item -LiteralPath $parameterPath }
    Remove-Item -LiteralPath $fixture
}
