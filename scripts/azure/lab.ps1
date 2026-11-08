#requires -Version 7.4
[CmdletBinding()]
param(
    [ValidateSet('Build', 'WhatIf', 'Deploy', 'Status', 'Scale', 'Start', 'Deallocate', 'Run', 'Download')]
    [string]$Action = 'Build',
    [string]$SubscriptionId,
    [string]$ResourceGroup,
    [string]$Location,
    [string]$ParametersFile,
    [int]$Capacity = -1,
    [ValidateSet('core', 'e1', 'e1-sqlserver', 'e2', 'e2-cluster', 'e3', 'e4-replay', 'm1', 'm2')][string]$Experiment = 'core',
    [string]$RunId,
    [string]$E4AttemptDirectory,
    [string]$E4LegacyResults,
    [string]$PostgresImage = 'docker.io/library/postgres:16.13',
    [string]$SqlServerImage = 'mcr.microsoft.com/mssql/server:2022-latest',
    [switch]$AcceptSqlServerLicense,
    [switch]$IncludeWorkingTree,
    [string]$OutputDirectory,
    [switch]$Apply,
    [switch]$AllowScaleIn
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$Template = Join-Path $Root 'infra\experiments\main.bicep'
if (-not $OutputDirectory) { $OutputDirectory = Join-Path $Root 'lab\results\azure' }

function Invoke-Azure([string[]]$Arguments) {
    if ($Arguments.Count -ge 3 -and ($Arguments[0..2] -join ' ') -eq 'deployment group what-if') {
        $Arguments += '--no-pretty-print'
    }
    $result = & az @Arguments --only-show-errors --output json
    if ($LASTEXITCODE -ne 0) { throw "Azure CLI failed: $($Arguments[0..1] -join ' '), exit $LASTEXITCODE" }
    if ($result) { return ($result -join "`n" | ConvertFrom-Json -Depth 100) }
}

function Assert-LabParameters([string]$Path) {
    $text = Get-Content -LiteralPath $Path -Raw
    if ($text -match 'REPLACE_') { throw 'Replace every placeholder in the parameter file before contacting Azure.' }
    $p = ($text | ConvertFrom-Json).parameters
    if ($p.prefix.value -cnotmatch '^[a-z][a-z0-9]{2,11}$') { throw 'prefix must contain 3-12 lowercase letters/digits, starting with a letter.' }
    if ($p.sshPublicKey.value -notmatch '^ssh-(ed25519|rsa) [A-Za-z0-9+/=]+(?: .*)?$') { throw 'Provide a public SSH key, never a private key.' }
    $date = [datetime]::ParseExact($p.expiresOn.value, 'yyyy-MM-dd', [cultureinfo]::InvariantCulture)
    if ($date.Date -le [datetime]::UtcNow.Date) { throw 'expiresOn must be a future review date.' }
    if ([double]$p.monthlyBudgetAmount.value -lt 1) { throw 'A positive monthly alert budget is required.' }
    $email = [System.Net.Mail.MailAddress]::new($p.budgetEmail.value)
    if ($email.Address -ne $p.budgetEmail.value -or $email.Host -like '*.invalid') { throw 'Provide a real budget notification address.' }
    if ($p.enableManagedPostgres.value) {
        [void][guid]::Parse($p.databaseAdminObjectId.value)
        if (-not $p.databaseAdminName.value) { throw 'Managed PostgreSQL requires an explicit Entra administrator.' }
    }
    return $p
}

function Assert-ScaleChange([int]$Current, [int]$Requested, [bool]$PermitReduction) {
    if ($Requested -notin @(0, 1, 2, 4, 8, 16)) { throw 'Capacity must be 0, 1, 2, 4, 8 or 16.' }
    if ($Requested -lt $Current -and -not $PermitReduction) {
        throw 'Scale-in deletes instances and local state. Export evidence, stop jobs, then pass -AllowScaleIn.'
    }
}

function Assert-RunResult($Response) {
    $messages = ($Response.value | ForEach-Object { $_.message }) -join "`n"
    $markers = [regex]::Matches($messages, '(?m)^AZURE_LAB_EXIT=(\d+)\s*$')
    if ($markers.Count -ne 1 -or $markers[0].Groups[1].Value -ne '0') {
        throw 'Guest execution failed or its completion marker is missing. Preserve the Run Command response and inspect uploaded evidence.'
    }
}

function Save-Json($Value, [string]$Path) {
    $Value | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $Path -Encoding utf8
}

function Invoke-LabAction {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
    if ($Action -eq 'Build') {
        & az bicep build --file $Template --outfile (Join-Path $OutputDirectory 'main.json')
        if ($LASTEXITCODE -ne 0) { throw 'Bicep build failed.' }
        return
    }
    [void][guid]::Parse($SubscriptionId)
    if ($ResourceGroup -notmatch '^[A-Za-z0-9_-]{1,90}$') { throw 'Specify a resource group name containing only letters, digits, hyphens or underscores.' }
    if ($Action -in @('Deploy', 'Scale', 'Start', 'Deallocate', 'Run') -and -not $Apply) {
        throw "$Action changes Azure resources or runs workloads. Review costs and rerun explicitly with -Apply."
    }
    if ($Action -eq 'Run') {
        if ($Experiment -eq 'e4-replay' -and (-not $E4AttemptDirectory -or -not $E4LegacyResults)) {
            throw 'E4 replay requires explicit -E4AttemptDirectory and -E4LegacyResults; it does not invoke a model.'
        }
        if ($Experiment -ne 'e4-replay' -and ($E4AttemptDirectory -or $E4LegacyResults)) {
            throw 'E4 input directories may only be supplied for e4-replay.'
        }
        if ($Experiment -eq 'e1-sqlserver' -and -not $AcceptSqlServerLicense) {
            throw 'Review the SQL Server Developer license and pass -AcceptSqlServerLicense explicitly before running this experiment.'
        }
        if ($SqlServerImage -cnotmatch '^mcr\.microsoft\.com/mssql/server(?::2022[A-Za-z0-9_.-]*|@sha256:[a-f0-9]{64})$') {
            throw 'Use an explicit official SQL Server 2022 tag or digest.'
        }
    }
    $context = @('--subscription', $SubscriptionId)
    $groupArgs = @('--resource-group', $ResourceGroup) + $context
    $parameters = $null
    if ($Action -in @('WhatIf', 'Deploy')) {
        if (-not $ParametersFile) { throw 'Specify a completed -ParametersFile.' }
        $ParametersFile = (Resolve-Path -LiteralPath $ParametersFile).Path
        $parameters = Assert-LabParameters $ParametersFile
    }
    $exists = Invoke-Azure (@('group', 'exists', '--name', $ResourceGroup) + $context)
    if (-not $exists) {
        if ($Action -ne 'Deploy') { throw 'The resource group does not exist. WhatIf needs an existing, dedicated group tagged purpose=book-experiments.' }
        if (-not $Location) { throw 'Specify -Location explicitly when creating the dedicated group.' }
        Invoke-Azure (@('group', 'create', '--name', $ResourceGroup, '--location', $Location,
            '--tags', 'purpose=book-experiments', 'owner=jmfloreszazo.com') + $context) | Out-Null
    }
    $group = Invoke-Azure (@('group', 'show', '--name', $ResourceGroup) + $context)
    if (-not $group.tags -or $group.tags.purpose -ne 'book-experiments') {
        throw 'Refusing to operate on a resource group without the purpose=book-experiments tag.'
    }
    $deploymentName = 'book-experiments'
    if ($Action -in @('WhatIf', 'Deploy')) {
        $verb = if ($Action -eq 'Deploy') { 'create' } else { 'what-if' }
        $arguments = @('deployment', 'group', $verb, '--name', $deploymentName,
            '--template-file', $Template, '--parameters', "@$ParametersFile") + $groupArgs
        if ($Action -eq 'Deploy') {
            $existingSets = @(Invoke-Azure (@('vmss', 'list') + $groupArgs))
            $expectedName = "$($parameters.prefix.value)-workers"
            foreach ($set in $existingSets) {
                if ($set.name -ne $expectedName) { throw 'A different scale set already exists in this dedicated group; do not change the environment prefix.' }
                $requested = if ($parameters.PSObject.Properties.Name -contains 'workerCount') { [int]$parameters.workerCount.value } else { 0 }
                Assert-ScaleChange $set.sku.capacity $requested $AllowScaleIn.IsPresent
            }
            # Always present the current plan; WhatIf never approves costs by itself.
            Invoke-Azure (@('deployment', 'group', 'what-if', '--name', $deploymentName,
                '--template-file', $Template, '--parameters', "@$ParametersFile") + $groupArgs) |
                ConvertTo-Json -Depth 100 | Write-Host
        }
        $response = Invoke-Azure $arguments
        Save-Json $response (Join-Path $OutputDirectory "$Action.json")
        if ($Action -eq 'Deploy' -and $response.properties.provisioningState -ne 'Succeeded') {
            throw 'Deployment did not reach Succeeded.'
        }
        return
    }
    $deployment = Invoke-Azure (@('deployment', 'group', 'show', '--name', $deploymentName) + $groupArgs)
    $outputs = $deployment.properties.outputs
    $runner = $outputs.runnerName.value
    $workers = $outputs.workerScaleSetName.value
    $storage = $outputs.storageAccountName.value
    $vmArgs = @('--name', $runner) + $groupArgs
    $vmssArgs = @('--name', $workers) + $groupArgs
    switch ($Action) {
        'Status' {
            $status = @{
                runner = Invoke-Azure (@('vm', 'get-instance-view') + $vmArgs)
                workers = Invoke-Azure (@('vmss', 'list-instances', '--expand', 'instanceView') + $vmssArgs)
                model = Invoke-Azure (@('vmss', 'show') + $vmssArgs)
            }
            Save-Json $status (Join-Path $OutputDirectory 'status.json')
            return $status
        }
        'Scale' {
            $current = Invoke-Azure (@('vmss', 'show') + $vmssArgs)
            Assert-ScaleChange $current.sku.capacity $Capacity $AllowScaleIn.IsPresent
            Invoke-Azure (@('vmss', 'scale', '--new-capacity', "$Capacity") + $vmssArgs) | Out-Null
            $instances = @(Invoke-Azure (@('vmss', 'list-instances', '--expand', 'instanceView') + $vmssArgs))
            Save-Json $instances (Join-Path $OutputDirectory "scale-$Capacity.json")
            if ($instances.Count -ne $Capacity -or @($instances | Where-Object { $_.provisioningState -ne 'Succeeded' }).Count) {
                throw 'Requested capacity and successfully provisioned instances differ.'
            }
            Write-Host "Provisioned $Capacity worker VMs. This does not start replicas or certify application readiness."
        }
        'Start' {
            Invoke-Azure (@('vm', 'start') + $vmArgs) | Out-Null
            $model = Invoke-Azure (@('vmss', 'show') + $vmssArgs)
            if ($model.sku.capacity -gt 0) { Invoke-Azure (@('vmss', 'start') + $vmssArgs) | Out-Null }
        }
        'Deallocate' {
            if (-not $AllowScaleIn) { throw 'Export evidence and stop jobs before deallocation; pass -AllowScaleIn to acknowledge interruption.' }
            $model = Invoke-Azure (@('vmss', 'show') + $vmssArgs)
            if ($model.sku.capacity -gt 0) { Invoke-Azure (@('vmss', 'deallocate') + $vmssArgs) | Out-Null }
            Invoke-Azure (@('vm', 'deallocate') + $vmArgs) | Out-Null
            Write-Warning 'Disks, NAT, public egress IP, storage and optional PostgreSQL still incur charges. Budget alerts do not cap spending.'
        }
        'Download' {
            if ($RunId -cnotmatch '^[a-z0-9-]{1,60}$') { throw 'Specify the recorded lowercase run ID.' }
            Invoke-Azure (@('storage', 'blob', 'download', '--auth-mode', 'login', '--account-name', $storage,
                '--container-name', 'evidence', '--name', "$RunId/evidence.tar.gz",
                '--file', (Join-Path $OutputDirectory "$RunId-evidence.tar.gz"), '--overwrite', 'false') + $context) | Out-Null
        }
        'Run' {
            if (-not $RunId) { $RunId = [datetime]::UtcNow.ToString('yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8) }
            if ($RunId -cnotmatch '^[a-z0-9-]{1,60}$') { throw 'Run ID must contain 1-60 lowercase letters, digits or hyphens.' }
            if ($PostgresImage -cnotmatch '^docker.io/library/postgres(?::[A-Za-z0-9_.-]+|@sha256:[a-f0-9]{64})$') { throw 'Use an explicit official PostgreSQL tag or digest.' }
            $runFolder = Join-Path $OutputDirectory $RunId
            if (Test-Path -LiteralPath $runFolder) { throw 'Run directory already exists; choose a fresh run ID.' }
            New-Item -ItemType Directory -Path $runFolder | Out-Null
            $commit = (& git -C $Root rev-parse HEAD).Trim()
            if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[a-f0-9]{40}$') { throw 'Cannot determine the source commit.' }
            $archive = Join-Path $runFolder 'source.tar'
            $sourceDirty = $false
            if ($IncludeWorkingTree) {
                & python (Join-Path $PSScriptRoot 'export-source.py') --output $archive
                if ($LASTEXITCODE -ne 0) { throw 'Explicit working-tree source export failed.' }
                $sourceRecord = Get-Content -LiteralPath ([IO.Path]::ChangeExtension($archive, '.json')) -Raw | ConvertFrom-Json
                if ($sourceRecord.sourceCommit -ne $commit) { throw 'Source HEAD changed during export.' }
                $sourceDirty = $sourceRecord.worktreeDirty
            } else {
                & git -C $Root diff --quiet HEAD -- lab
                if ($LASTEXITCODE -ne 0) { throw 'Commit lab changes locally or explicitly use -IncludeWorkingTree. No push is needed.' }
                & git -C $Root archive --format=tar "--output=$archive" HEAD
                if ($LASTEXITCODE -ne 0) { throw 'Source export failed.' }
            }
            $e4Digest = ''
            if ($Experiment -eq 'e4-replay') {
                $inputs = Join-Path $runFolder 'e4-inputs.tar'
                $inputRecord = & python (Join-Path $PSScriptRoot 'e4-inputs.py') pack `
                    --attempt $E4AttemptDirectory --legacy $E4LegacyResults --output $inputs
                if ($LASTEXITCODE -ne 0) { throw 'E4 replay input validation failed; no candidate will run.' }
                $inputRecord = ($inputRecord -join "`n") | ConvertFrom-Json
                $e4Digest = $inputRecord.archiveSha256
                Save-Json $inputRecord (Join-Path $runFolder 'e4-inputs.json')
                Invoke-Azure (@('storage', 'blob', 'upload', '--auth-mode', 'login', '--account-name', $storage,
                    '--container-name', 'source', '--name', "$RunId/e4-inputs.tar", '--file', $inputs,
                    '--overwrite', 'false') + $context) | Out-Null
            }
            $digest = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
            Invoke-Azure (@('storage', 'blob', 'upload', '--auth-mode', 'login', '--account-name', $storage,
                '--container-name', 'source', '--name', "$RunId/source.tar", '--file', $archive,
                '--overwrite', 'false') + $context) | Out-Null
            $launcherPath = Join-Path $PSScriptRoot 'run-experiment.sh'
            $launcher = [Convert]::ToBase64String([IO.File]::ReadAllBytes($launcherPath))
            $remote = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'remote-run.sh') -Raw
            $values = @{
                STORAGE = $storage
                CLIENT_ID = $outputs.runnerIdentityClientId.value
                RUN_ID = $RunId
                SOURCE_SHA256 = $digest
                COMMIT = $commit
                SOURCE_DIRTY = $(if ($sourceDirty) { 'true' } else { 'false' })
                EXPERIMENT = $Experiment
                E4_INPUT_SHA256 = $e4Digest
                LAUNCHER = $launcher
                PG_IMAGE = $PostgresImage
                SQL_IMAGE = $SqlServerImage
                ACCEPT_SQL_EULA = $(if ($Experiment -eq 'e1-sqlserver' -and $AcceptSqlServerLicense) { 'Y' } else { 'N' })
            }
            foreach ($key in $values.Keys) { $remote = $remote.Replace("__${key}__", $values[$key]) }
            $remotePath = Join-Path $runFolder 'remote-run.sh'
            [IO.File]::WriteAllText($remotePath, $remote.Replace("`r`n", "`n"), [Text.UTF8Encoding]::new($false))
            Save-Json @{ commit = $commit; sourceSha256 = $digest; runId = $RunId; experiment = $Experiment
                includeWorkingTree = $IncludeWorkingTree.IsPresent; worktreeDirty = $sourceDirty
                e4InputSha256 = $e4Digest; newModelInvocation = $false
                sqlServerLicenseAccepted = ($Experiment -eq 'e1-sqlserver' -and $AcceptSqlServerLicense.IsPresent)
                launcherSha256 = (Get-FileHash -LiteralPath $launcherPath -Algorithm SHA256).Hash
                classification = 'Azure-hosted single-VM synthetic smoke; not distributed E3' } (Join-Path $runFolder 'request.json')
            $response = Invoke-Azure (@('vm', 'run-command', 'invoke', '--command-id', 'RunShellScript',
                '--scripts', "@$remotePath") + $vmArgs)
            Save-Json $response (Join-Path $runFolder 'run-command.json')
            Assert-RunResult $response
            Write-Host "Run $RunId completed. Download its evidence archive; no experiment status was promoted."
        }
    }
}

if ($MyInvocation.InvocationName -ne '.') { Invoke-LabAction }
