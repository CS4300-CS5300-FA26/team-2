run "key_vault_uses_rbac_not_access_policies" {
  command = plan

  assert {
    condition     = azurerm_key_vault.main.rbac_authorization_enabled == true
    error_message = "Key Vault must use RBAC authorization so the role assignment below actually grants access."
  }
}

run "backend_identity_granted_secrets_user_role" {
  command = plan

  assert {
    condition     = azurerm_role_assignment.backend_keyvault_secrets_user.role_definition_name == "Key Vault Secrets User"
    error_message = "The backend Web App's system-assigned identity must hold Key Vault Secrets User, or its @Microsoft.KeyVault(...) app-setting references fail to resolve."
  }
}

run "key_vault_blocks_public_network_access" {
  command = plan

  assert {
    condition     = azurerm_key_vault.main.network_acls[0].default_action == "Deny"
    error_message = "Key Vault must default-deny network access; only the AKS subnet should reach it."
  }
}
