run "postgres_is_burstable_b1ms" {
  command = plan

  assert {
    condition     = azurerm_postgresql_flexible_server.main.sku_name == "B_Standard_B1ms"
    error_message = "Postgres Flexible Server must be Burstable B1MS to match the free-12-months allocation."
  }
}

run "postgres_has_no_public_network_access" {
  command = plan

  assert {
    condition     = azurerm_postgresql_flexible_server.main.public_network_access_enabled == false
    error_message = "Postgres must not be reachable from the public internet; it sits on the private data subnet only."
  }
}

run "postgres_has_no_high_availability" {
  command = plan

  assert {
    condition     = length(azurerm_postgresql_flexible_server.main.high_availability) == 0
    error_message = "No zone-redundant standby per the ADR; this is the accepted single point of failure, not an oversight."
  }
}
