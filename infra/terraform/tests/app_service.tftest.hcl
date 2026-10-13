run "service_plan_is_basic_b1" {
  command = plan

  assert {
    condition     = azurerm_service_plan.main.sku_name == "B1"
    error_message = "App Service Plan must stay on Basic B1 (~$13.14/mo); a pricier SKU wasn't costed."
  }
}

run "service_plan_runs_two_instances" {
  command = plan

  assert {
    condition     = azurerm_service_plan.main.worker_count == 2
    error_message = "App Service Plan must run 2 instances (worker_count is per-plan, shared by both Web Apps)."
  }
}

run "backend_always_on" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.backend.site_config[0].always_on == true
    error_message = "Backend must have always_on enabled for a 24/7 uptime target."
  }
}

run "frontend_always_on" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.frontend.site_config[0].always_on == true
    error_message = "Frontend must have always_on enabled for a 24/7 uptime target."
  }
}

run "backend_health_check_path_matches_django" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.backend.site_config[0].health_check_path == "/healthz/"
    error_message = "Health check path must match backend/pathfinder/health.py's healthz route."
  }
}

run "backend_python_version_pinned" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.backend.site_config[0].application_stack[0].python_version == "3.12"
    error_message = "Backend Python runtime version must be pinned, not left to float to whatever Oryx defaults to."
  }
}

run "frontend_node_version_pinned" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.frontend.site_config[0].application_stack[0].node_version == "20-lts"
    error_message = "Frontend Node runtime version must be pinned, not left to float to whatever Oryx defaults to."
  }
}

run "backend_routes_all_traffic_through_vnet" {
  command = plan

  # virtual_network_subnet_id itself is "known after apply" in a plan-only
  # run (it's a cross-resource reference), so this asserts the companion
  # site_config flag instead, which is a plain bool known at plan time.
  assert {
    condition     = azurerm_linux_web_app.backend.site_config[0].vnet_route_all_enabled == true
    error_message = "Backend must route all outbound traffic through VNet integration to reach the private Postgres server, Key Vault, and Storage."
  }
}

run "backend_has_system_assigned_identity" {
  command = plan

  assert {
    condition     = azurerm_linux_web_app.backend.identity[0].type == "SystemAssigned"
    error_message = "Backend needs a system-assigned managed identity for Key Vault reference auth."
  }
}

run "backend_secrets_come_from_key_vault_references" {
  command = plan

  assert {
    condition = (
      strcontains(azurerm_linux_web_app.backend.app_settings["SECRET_KEY"], "@Microsoft.KeyVault(") &&
      strcontains(azurerm_linux_web_app.backend.app_settings["DATABASE_URL"], "@Microsoft.KeyVault(")
    )
    error_message = "SECRET_KEY and DATABASE_URL must be Key Vault references, not plaintext values in Terraform state."
  }
}
