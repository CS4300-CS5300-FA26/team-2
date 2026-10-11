output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "postgres_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}

output "storage_account_name" {
  value = azurerm_storage_account.media.name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "key_vault_name" {
  description = "Key Vault name, not its URI."
  value       = azurerm_key_vault.main.name
}

output "app_service_plan_name" {
  value = azurerm_service_plan.main.name
}

output "backend_default_hostname" {
  description = "Public URL of the Django API (App Service)."
  value       = azurerm_linux_web_app.backend.default_hostname
}

output "frontend_default_hostname" {
  description = "Public URL of the React frontend (App Service)."
  value       = azurerm_linux_web_app.frontend.default_hostname
}
