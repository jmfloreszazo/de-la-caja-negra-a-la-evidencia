param name string
param location string
param tags object
param subnetId string
param vnetId string
@minLength(36)
param adminObjectId string
@minLength(1)
param adminName string
param adminType string
param haMode string

resource dns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${name}.private.postgres.database.azure.com'
  location: 'global'
}
resource link 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dns
  name: 'lab'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: { id: vnetId }
  }
}
resource server 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: name
  location: location
  tags: tags
  sku: { name: 'Standard_D2ds_v5', tier: 'GeneralPurpose' }
  properties: {
    version: '16'
    createMode: 'Default'
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
      tenantId: tenant().tenantId
    }
    storage: { storageSizeGB: 32, autoGrow: 'Disabled' }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    highAvailability: { mode: haMode }
    network: {
      delegatedSubnetResourceId: subnetId
      privateDnsZoneArmResourceId: dns.id
      publicNetworkAccess: 'Disabled'
    }
  }
  dependsOn: [link]
}
resource admin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2024-08-01' = {
  parent: server
  name: adminObjectId
  properties: {
    principalName: adminName
    principalType: adminType
    tenantId: tenant().tenantId
  }
}
output fqdn string = server.properties.fullyQualifiedDomainName
