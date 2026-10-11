terraform {
  backend "azurerm" {
    resource_group_name  = "rg-pathfinder-tfstate"
    storage_account_name = "pathfinderstfstate"
    container_name       = "tfstate"
    key                  = "pathfinder.tfstate"

    # Shared-key auth is disabled on this storage account; state access
    # is gated by Azure AD identity (Storage Blob Data Contributor role)
    # instead of a static key or a network/IP rule. Works from any
    # network, survives this laptop changing wifi.
    use_azuread_auth = true
  }
}
