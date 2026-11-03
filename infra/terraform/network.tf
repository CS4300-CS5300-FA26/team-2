resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location
}

resource "azurerm_virtual_network" "main" {
  name                = "vnet-${var.project_name}-${var.environment}"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
}

resource "azurerm_subnet" "app_service" {
  # Name unchanged from the live "snet-aks" value on purpose: Azure subnet
  # names are immutable in place, so renaming this string would force a
  # destroy/recreate of an already-live subnet. Only the Terraform label
  # (see the moved block in versions.tf) and the delegation changed.
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.0.0/20"]

  # Required for the Key Vault/Storage network rules in keyvault.tf and
  # storage.tf to recognize traffic from this subnet; without these, the
  # App Service VNet-integrated outbound traffic hits those services'
  # public endpoints over the open internet path instead of the Azure
  # backbone, and the VNet-scoped allow-list on each service won't match.
  service_endpoints = ["Microsoft.Storage", "Microsoft.KeyVault"]

  # Delegating this subnet to App Service is what makes VNet Integration
  # possible: the backend Web App (app_service.tf) uses this subnet for
  # outbound traffic to reach the private Postgres server, Key Vault, and
  # Storage over the VNet instead of the public internet.
  delegation {
    name = "app-service-vnet-integration"

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}

resource "azurerm_subnet" "data" {
  name                 = "snet-data"
  resource_group_name  = azurerm_resource_group.main.name
  virtual_network_name = azurerm_virtual_network.main.name
  address_prefixes     = ["10.0.16.0/24"]

  delegation {
    name = "postgres-flexible-server"

    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

# No port 22 rule exists on purpose. This subnet only carries App Service
# VNet-integration outbound traffic, not SSH-able compute; see the ADR's
# security table.
resource "azurerm_network_security_group" "app_service" {
  # Name unchanged from the live "nsg-pathfinder-aks" value for the same
  # immutable-name reason as the subnet above.
  name                = "nsg-${var.project_name}-aks"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  security_rule {
    name                       = "AllowHTTPSInbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPInbound"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "DenyAllInbound"
    priority                   = 4096
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_subnet_network_security_group_association" "app_service" {
  subnet_id                 = azurerm_subnet.app_service.id
  network_security_group_id = azurerm_network_security_group.app_service.id
}
