# Azure Communication Services Email, used by backend/pathfinder/acs_email.py.
# Sender is an Azure-managed domain (<guid>.azurecomm.net), so no DNS records are
# needed. The Web App authenticates with its managed identity (role below), so no
# connection string or key exists.

resource "azurerm_email_communication_service" "main" {
  name                = "acs-email-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"
}

resource "azurerm_email_communication_service_domain" "managed" {
  name              = "AzureManagedDomain"
  email_service_id  = azurerm_email_communication_service.main.id
  domain_management = "AzureManaged"
}

resource "azurerm_communication_service" "main" {
  name                = "acs-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  data_location       = "United States"
}

resource "azurerm_communication_service_email_domain_association" "managed" {
  communication_service_id = azurerm_communication_service.main.id
  email_service_domain_id  = azurerm_email_communication_service_domain.managed.id
}

# Lets the backend's identity send mail through this Communication Service only.
resource "azurerm_role_assignment" "backend_acs_email_sender" {
  scope                = azurerm_communication_service.main.id
  role_definition_name = "Communication and Email Service Owner"
  principal_id         = azurerm_linux_web_app.backend.identity[0].principal_id
}
