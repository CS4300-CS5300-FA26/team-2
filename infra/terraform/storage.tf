resource "azurerm_storage_account" "media" {
  name                            = "st${var.project_name}${var.environment}media"
  resource_group_name             = azurerm_resource_group.main.name
  location                        = azurerm_resource_group.main.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  # Public endpoint stays reachable (Private Endpoints cost ~$7-8/mo,
  # not worth it against the free-tier budget); network_rules below is
  # the actual gate, default-deny except the App Service VNet-integration
  # subnet (where the Django backend runs) and trusted first-party Azure
  # services. VNet Service Endpoint pattern, not Private Link.
  public_network_access_enabled = true

  network_rules {
    default_action             = "Deny"
    bypass                     = ["AzureServices"]
    virtual_network_subnet_ids = [azurerm_subnet.app_service.id]
  }
}

resource "azurerm_storage_container" "media" {
  name                  = "media"
  storage_account_id    = azurerm_storage_account.media.id
  container_access_type = "private"
}

# Lets the backend Web App's system-assigned identity read/write blobs via
# Azure AD auth (DefaultAzureCredential in prod.py), no account key needed.
# Scoped to just this storage account, same pattern as the Key Vault role
# assignment in keyvault.tf.
resource "azurerm_role_assignment" "backend_storage_blob_data_contributor" {
  scope                = azurerm_storage_account.media.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}
