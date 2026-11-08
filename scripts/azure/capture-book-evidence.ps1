#requires -Version 7.4
[CmdletBinding()]
param(
    [Parameter(Mandatory)][guid]$SubscriptionId,
    [Parameter(Mandatory)][string]$ResourceGroup,
    [Parameter(Mandatory)][string]$RunnerName,
    [Parameter(Mandatory)][string]$WorkerScaleSetName,
    [Parameter(Mandatory)][string]$StorageAccountName,
    [string]$DeploymentName = 'book-experiments',
    [Parameter(Mandatory)][string]$OutputDirectory
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Choose a new capture directory; earlier evidence must remain unchanged.' }
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$commands = @(
    @{name='resources'; args=@('resource','list','--resource-group',$ResourceGroup,'--query','sort_by(@, &name)[].{name:name,type:type,location:location}')},
    @{name='deployment'; args=@('deployment','group','show','--resource-group',$ResourceGroup,'--name',$DeploymentName,'--query','{name:name,state:properties.provisioningState,timestamp:properties.timestamp}')},
    @{name='runner'; args=@('vm','get-instance-view','--resource-group',$ResourceGroup,'--name',$RunnerName,'--query','{name:name,location:location,size:hardwareProfile.vmSize,statuses:instanceView.statuses[].code}')},
    @{name='workers'; args=@('vmss','show','--resource-group',$ResourceGroup,'--name',$WorkerScaleSetName,'--query','{name:name,location:location,capacity:sku.capacity,size:sku.name}')},
    @{name='worker-instances'; args=@('vmss','list-instances','--resource-group',$ResourceGroup,'--name',$WorkerScaleSetName,'--query','[].{instanceId:instanceId,state:provisioningState}')},
    @{name='storage'; args=@('storage','account','show','--resource-group',$ResourceGroup,'--name',$StorageAccountName,'--query','{name:name,location:location,httpsOnly:enableHttpsTrafficOnly,minimumTlsVersion:minimumTlsVersion,sharedKeyAccess:allowSharedKeyAccess,publicBlobAccess:allowBlobPublicAccess}')}
)
$records = @()
$overall = 'PASS'
try {
    foreach ($command in $commands) {
        $arguments = $command.args + @('--subscription', $SubscriptionId.ToString(), '--only-show-errors', '--output', 'json')
        $stdout = Join-Path $OutputDirectory ($command.name + '.json')
        $stderr = Join-Path $OutputDirectory ($command.name + '.stderr.txt')
        $started = [datetime]::UtcNow.ToString('o')
        & az @arguments 1> $stdout 2> $stderr
        $code = $LASTEXITCODE
        $records += [ordered]@{ name=$command.name; argv=@('az') + $arguments; startedUtc=$started
            finishedUtc=[datetime]::UtcNow.ToString('o'); exitCode=$code; stdout=[IO.Path]::GetFileName($stdout)
            stderr=[IO.Path]::GetFileName($stderr); sha256=(Get-FileHash $stdout -Algorithm SHA256).Hash.ToLowerInvariant() }
        if ($code -ne 0) { throw "Read-only Azure capture failed: $($command.name); original output retained." }
        $null = Get-Content -LiteralPath $stdout -Raw | ConvertFrom-Json
    }
} catch {
    $overall = 'FAIL'
    throw
} finally {
    [ordered]@{ classification='READ_ONLY_AZURE_CONTROL_PLANE_CAPTURE_NOT_WORKLOAD_EVIDENCE'; status=$overall
        subscriptionId=$SubscriptionId.ToString(); resourceGroup=$ResourceGroup; commands=$records
        limitations=@('Projected live CLI output, not a portal screenshot or performance result.',
            'Resource state is time-specific. Deallocated compute can still incur disk/network/storage costs.',
            'No secrets, keys or user identity fields were requested. Standard CLI formatting is retained.') } |
        ConvertTo-Json -Depth 12 | Set-Content (Join-Path $OutputDirectory 'capture.json') -Encoding utf8
}
Write-Output "Read-only Azure book capture: $overall ($($records.Count) commands)."
