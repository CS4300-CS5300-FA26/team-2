run "no_ssh_open_to_the_world" {
  command = plan

  assert {
    condition = alltrue([
      for rule in azurerm_network_security_group.app_service.security_rule :
      !(rule.destination_port_range == "22" && contains(["*", "0.0.0.0/0"], rule.source_address_prefix))
    ])
    error_message = "No NSG rule may open port 22 to all source addresses."
  }
}

run "resource_group_in_correct_region" {
  command = plan

  assert {
    condition     = azurerm_resource_group.main.location == "westus"
    error_message = "Resource group must be in westus (the only quota- and policy-allowed region confirmed for this subscription)."
  }
}
