data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "kv-${var.project_name}-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true

  # Deliberately off: the ADR's default is tear-down-after-grading, and
  # purge protection blocks clean deletion for the retention period. Flip
  # to true if the project's disposition changes to "keep running".
  purge_protection_enabled   = false
  soft_delete_retention_days = 7

  # Public endpoint stays reachable (Private Endpoints cost ~$7-8/mo,
  # not worth it against the free-tier budget); network_acls below is
  # the actual gate, default-deny except the App Service VNet-integration
  # subnet and trusted first-party Azure services. VNet Service Endpoint
  # pattern, not Private Link.
  public_network_access_enabled = true

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Deny"
    virtual_network_subnet_ids = [azurerm_subnet.app_service.id]
  }
}

resource "azurerm_role_assignment" "backend_keyvault_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}

# Terraform provisions the Key Vault itself and grants the backend Web
# App's system-assigned identity read access (above), which is also what
# App Service's native "@Microsoft.KeyVault(...)" app-setting references
# (app_service.tf) authenticate as. It does not generate or write secret
# values, those are set via `az keyvault secret set` by whoever operates
# this, not stored in Terraform state.
