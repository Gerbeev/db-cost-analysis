# Read-only Azure resource inventory. No cloud resources are modified.
# Requires Azure CLI, an existing az login, and read access to the subscription.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$SubscriptionId,
    [string]$OutFile = "reports/azure_workspace_inventory.csv"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    throw "Azure CLI (az) is not installed or is not on PATH."
}

# 'az resource list' uses the built-in Azure Resource Manager interface (no extension).
$json = & az resource list --subscription $SubscriptionId --resource-type Microsoft.Databricks/workspaces --output json --only-show-errors
if ($LASTEXITCODE -ne 0) {
    throw "Azure Resource Manager inventory query failed. Check Azure CLI login and subscription permissions."
}

$resources = @($json | ConvertFrom-Json)
[array]$records = foreach ($resource in $resources) {
    $managedGroup = ""
    $dbWorkspaceId = ""
    if ($null -ne $resource.properties) {
        if ($null -ne $resource.properties.managedResourceGroupId) {
            $managedGroup = [string]$resource.properties.managedResourceGroupId
        }
        if ($null -ne $resource.properties.workspaceId) {
            $dbWorkspaceId = [string]$resource.properties.workspaceId
        }
    }
    $sku = if ($null -ne $resource.sku -and $null -ne $resource.sku.name) { [string]$resource.sku.name } else { "" }
    [pscustomobject]@{
        subscription_id = $SubscriptionId
        workspace_name = [string]$resource.name
        databricks_workspace_id = $dbWorkspaceId
        azure_resource_id = [string]$resource.id
        resource_group = [string]$resource.resourceGroup
        managed_resource_group_id = $managedGroup
        location = [string]$resource.location
        sku = $sku
    }
}

$destination = if ([System.IO.Path]::IsPathRooted($OutFile)) {
    [System.IO.Path]::GetFullPath($OutFile)
} else {
    [System.IO.Path]::GetFullPath((Join-Path (Get-Location).Path $OutFile))
}
$folder = Split-Path -Parent $destination
New-Item -Path $folder -ItemType Directory -Force | Out-Null
if ($records.Count -eq 0) {
    'subscription_id,workspace_name,databricks_workspace_id,azure_resource_id,resource_group,managed_resource_group_id,location,sku' |
        Set-Content -LiteralPath $destination -Encoding UTF8
    Write-Warning "No Azure Databricks workspaces found in the selected subscription."
} else {
    $records | Export-Csv -LiteralPath $destination -NoTypeInformation -Encoding UTF8
}
Write-Host "Read-only Azure Databricks workspace inventory: $destination"
Write-Host "Workspace count: $($records.Count)"
