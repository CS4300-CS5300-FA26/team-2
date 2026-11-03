run "storage_account_blocks_public_blob_access" {
  command = plan

  assert {
    condition     = azurerm_storage_account.media.allow_nested_items_to_be_public == false
    error_message = "Storage account must not allow public blob access; resumes are user-uploaded PII."
  }
}

run "storage_account_enforces_tls12" {
  command = plan

  assert {
    condition     = azurerm_storage_account.media.min_tls_version == "TLS1_2"
    error_message = "Storage account must require TLS 1.2 minimum."
  }
}

run "storage_account_blocks_public_network_access" {
  command = plan

  assert {
    condition     = azurerm_storage_account.media.network_rules[0].default_action == "Deny"
    error_message = "Storage account must default-deny network access; resumes are PII, only the AKS subnet should reach it."
  }
}
