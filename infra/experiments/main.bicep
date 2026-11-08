targetScope = 'resourceGroup'

@minLength(3)
@maxLength(12)
param prefix string
param location string = resourceGroup().location
@description('Public SSH key only. No public SSH endpoint is created.')
param sshPublicKey string
param adminUsername string = 'laboperator'
param owner string = 'jmfloreszazo.com'
@description('Review date, not an automatic deletion schedule.')
param expiresOn string
@allowed([0, 1, 2, 4, 8, 16])
param workerCount int = 0
param vmSize string = 'Standard_D4s_v5'
@description('Leave empty for regional placement; choose supported zones explicitly for multi-zone trials.')
param workerZones array = []
param imageVersion string = 'latest'
param enableManagedPostgres bool = false
@allowed(['Disabled', 'SameZone', 'ZoneRedundant'])
param postgresHaMode string = 'Disabled'
@description('Entra object ID of the operator administering the optional disposable managed database.')
param databaseAdminObjectId string = ''
param databaseAdminName string = ''
@allowed(['User', 'Group', 'ServicePrincipal'])
param databaseAdminType string = 'User'
@minValue(1)
param monthlyBudgetAmount int
param budgetEmail string
param budgetStartDate string = utcNow('yyyy-MM-01')

var tags = {
  owner: owner
  purpose: 'book-experiments'
  evidenceClass: 'unverified-infrastructure'
  expiresOn: expiresOn
}
var suffix = uniqueString(resourceGroup().id, prefix)
var cloudInit = base64(loadTextContent('cloud-init.yaml'))
var image = {
  publisher: 'Canonical'
  offer: 'ubuntu-24_04-lts'
  sku: 'server'
  version: imageVersion
}
var blobReader = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1')
var blobWriter = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')

resource runnerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-runner-id'
  location: location
  tags: tags
}
resource workerIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-worker-id'
  location: location
  tags: tags
}
resource outboundIp 'Microsoft.Network/publicIPAddresses@2024-05-01' = {
  name: '${prefix}-egress-ip'
  location: location
  tags: tags
  sku: { name: 'Standard' }
  properties: { publicIPAllocationMethod: 'Static' }
}
resource nat 'Microsoft.Network/natGateways@2024-05-01' = {
  name: '${prefix}-egress'
  location: location
  tags: tags
  sku: { name: 'Standard' }
  properties: {
    publicIpAddresses: [{ id: outboundIp.id }]
    idleTimeoutInMinutes: 10
  }
}
resource nsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: '${prefix}-compute-nsg'
  location: location
  tags: tags
  properties: {
    securityRules: [{
      name: 'DenyInternetInbound'
      properties: {
        priority: 100
        access: 'Deny'
        direction: 'Inbound'
        protocol: '*'
        sourceAddressPrefix: 'Internet'
        sourcePortRange: '*'
        destinationAddressPrefix: '*'
        destinationPortRange: '*'
      }
    }]
  }
}
resource vnet 'Microsoft.Network/virtualNetworks@2024-05-01' = {
  name: '${prefix}-vnet'
  location: location
  tags: tags
  properties: {
    addressSpace: { addressPrefixes: ['10.76.0.0/16'] }
    subnets: [
      {
        name: 'runner'
        properties: {
          addressPrefix: '10.76.0.0/24'
          networkSecurityGroup: { id: nsg.id }
          natGateway: { id: nat.id }
        }
      }
      {
        name: 'workers'
        properties: {
          addressPrefix: '10.76.1.0/24'
          networkSecurityGroup: { id: nsg.id }
          natGateway: { id: nat.id }
        }
      }
      {
        name: 'database'
        properties: {
          addressPrefix: '10.76.2.0/24'
          delegations: [{
            name: 'postgres'
            properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' }
          }]
        }
      }
    ]
  }
}
resource runnerNic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: '${prefix}-runner-nic'
  location: location
  tags: tags
  properties: {
    ipConfigurations: [{
      name: 'private'
      properties: {
        privateIPAllocationMethod: 'Dynamic'
        subnet: { id: '${vnet.id}/subnets/runner' }
      }
    }]
  }
}
resource runner 'Microsoft.Compute/virtualMachines@2024-07-01' = {
  name: '${prefix}-runner'
  location: location
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${runnerIdentity.id}': {} }
  }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    storageProfile: {
      imageReference: image
      osDisk: {
        createOption: 'FromImage'
        diskSizeGB: 128
        managedDisk: { storageAccountType: 'Premium_LRS' }
      }
    }
    osProfile: {
      computerName: '${prefix}-runner'
      adminUsername: adminUsername
      customData: cloudInit
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: { publicKeys: [{ path: '/home/${adminUsername}/.ssh/authorized_keys', keyData: sshPublicKey }] }
      }
    }
    networkProfile: { networkInterfaces: [{ id: runnerNic.id }] }
    securityProfile: {
      securityType: 'TrustedLaunch'
      uefiSettings: { secureBootEnabled: true, vTpmEnabled: true }
    }
    diagnosticsProfile: { bootDiagnostics: { enabled: true } }
  }
}
resource workers 'Microsoft.Compute/virtualMachineScaleSets@2024-07-01' = {
  name: '${prefix}-workers'
  location: location
  tags: tags
  zones: workerZones
  sku: { name: vmSize, tier: 'Standard', capacity: workerCount }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${workerIdentity.id}': {} }
  }
  properties: {
    orchestrationMode: 'Uniform'
    singlePlacementGroup: false
    upgradePolicy: { mode: 'Manual' }
    overprovision: false
    virtualMachineProfile: {
      storageProfile: {
        imageReference: image
        osDisk: {
          createOption: 'FromImage'
          diskSizeGB: 128
          managedDisk: { storageAccountType: 'Premium_LRS' }
        }
      }
      osProfile: {
        computerNamePrefix: '${prefix}-w'
        adminUsername: adminUsername
        customData: cloudInit
        linuxConfiguration: {
          disablePasswordAuthentication: true
          ssh: { publicKeys: [{ path: '/home/${adminUsername}/.ssh/authorized_keys', keyData: sshPublicKey }] }
        }
      }
      networkProfile: {
        networkInterfaceConfigurations: [{
          name: 'private'
          properties: {
            primary: true
            ipConfigurations: [{
              name: 'private'
              properties: {
                primary: true
                subnet: { id: '${vnet.id}/subnets/workers' }
              }
            }]
          }
        }]
      }
      securityProfile: {
        securityType: 'TrustedLaunch'
        uefiSettings: { secureBootEnabled: true, vTpmEnabled: true }
      }
      diagnosticsProfile: { bootDiagnostics: { enabled: true } }
    }
  }
}
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: 'lab${suffix}'
  location: location
  tags: tags
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
  }
}
resource blobs 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    isVersioningEnabled: true
    deleteRetentionPolicy: { enabled: true, days: 30 }
    containerDeleteRetentionPolicy: { enabled: true, days: 30 }
  }
}
resource source 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobs
  name: 'source'
  properties: { publicAccess: 'None' }
}
resource evidence 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobs
  name: 'evidence'
  properties: { publicAccess: 'None' }
}
resource sourceReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: source
  name: guid(source.id, runnerIdentity.id, blobReader)
  properties: {
    principalId: runnerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: blobReader
  }
}
resource evidenceWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: evidence
  name: guid(evidence.id, runnerIdentity.id, blobWriter)
  properties: {
    principalId: runnerIdentity.properties.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: blobWriter
  }
}
module database 'postgres.bicep' = if (enableManagedPostgres) {
  name: '${prefix}-database'
  params: {
    name: '${prefix}-${suffix}'
    location: location
    tags: tags
    subnetId: '${vnet.id}/subnets/database'
    vnetId: vnet.id
    adminObjectId: databaseAdminObjectId
    adminName: databaseAdminName
    adminType: databaseAdminType
    haMode: postgresHaMode
  }
}
resource budget 'Microsoft.Consumption/budgets@2023-05-01' = {
  name: '${prefix}-monthly'
  properties: {
    category: 'Cost'
    amount: monthlyBudgetAmount
    timeGrain: 'Monthly'
    timePeriod: { startDate: budgetStartDate }
    notifications: {
      Actual80Percent: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 80
        thresholdType: 'Actual'
        contactEmails: [budgetEmail]
      }
      Forecast100Percent: {
        enabled: true
        operator: 'GreaterThanOrEqualTo'
        threshold: 100
        thresholdType: 'Forecasted'
        contactEmails: [budgetEmail]
      }
    }
  }
}

output runnerName string = runner.name
output workerScaleSetName string = workers.name
output storageAccountName string = storage.name
output runnerIdentityClientId string = runnerIdentity.properties.clientId
output postgresFqdn string = enableManagedPostgres ? database!.outputs.fqdn : ''
output evidenceClassification string = 'Infrastructure only; no E1-E4 acceptance or measured scaling result.'
