# State-only renames from the AKS->App Service pivot. These resources are
# already live in Azure; without `moved` blocks, Terraform would plan a
# destroy of the old address and a create of the new one instead of an
# in-place rename, violating the "don't touch already-live resources"
# constraint from the ADR.
moved {
  from = azurerm_subnet.aks
  to   = azurerm_subnet.app_service
}

moved {
  from = azurerm_network_security_group.aks
  to   = azurerm_network_security_group.app_service
}

moved {
  from = azurerm_subnet_network_security_group_association.aks
  to   = azurerm_subnet_network_security_group_association.app_service
}
