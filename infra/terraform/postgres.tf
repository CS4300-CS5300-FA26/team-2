resource "azurerm_private_dns_zone" "postgres" {
  name                = "${var.project_name}.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_private_dns_zone_virtual_network_link" "postgres" {
  name                  = "pdnslink-${var.project_name}"
  private_dns_zone_name = azurerm_private_dns_zone.postgres.name
  virtual_network_id    = azurerm_virtual_network.main.id
  resource_group_name   = azurerm_resource_group.main.name
}

# Terraform must supply some initial admin password to create the server
# at all, there's no way to defer that to a later `az` step the way the
# Key Vault secrets are (see keyvault.tf). This value still lands in
# Terraform state as a result.
#
# REQUIRED POST-APPLY STEP: rotate this immediately after `terraform apply`
# via `az postgres flexible-server update --name psql-<project>-<env>
# --resource-group rg-<project>-<env> --admin-password <new-password>`,
# then set the rotated value in Key Vault's DATABASE-URL secret (see
# keyvault.tf's comment on how secrets get populated). The value below
# becomes a stale placeholder the moment that rotation happens, not the
# real credential in use.
resource "random_password" "postgres_admin" {
  length  = 24
  special = true
}

resource "azurerm_postgresql_flexible_server" "main" {
  name                = "psql-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  sku_name   = "B_Standard_B1ms"
  version    = "16"
  storage_mb = 32768

  administrator_login    = "pathfinderadmin"
  administrator_password = random_password.postgres_admin.result

  delegated_subnet_id           = azurerm_subnet.data.id
  private_dns_zone_id           = azurerm_private_dns_zone.postgres.id
  public_network_access_enabled = false

  # No zone-redundant standby. Accepted single point of failure, see the ADR.
  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

resource "azurerm_postgresql_flexible_server_database" "app" {
  name      = var.project_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "UTF8"
}
