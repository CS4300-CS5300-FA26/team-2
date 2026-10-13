# Single public origin in front of the frontend and backend App Services
# (deployment/gateway.Dockerfile, deployment/nginx.gateway.conf.template),
# replacing the proxying the old Railway nginx container did before the
# AKS/App Service split put the two apps on separate azurewebsites.net
# origins with no shared gateway. The custom domain (custom_domain.tf)
# binds here, not to the frontend app, so path-finders.app is this
# gateway's origin.

# ACR names are globally unique across all of Azure (they become
# <name>.azurecr.io), not just within this subscription -- "acrpathfinderprod"
# collided with someone else's existing registry, hence the random suffix.
resource "random_string" "acr_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "azurerm_container_registry" "main" {
  name                = "acr${var.project_name}${var.environment}${random_string.acr_suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"

  # Only for CI to push images -- the gateway app itself pulls via its own
  # managed identity (AcrPull role assignment below), not this account.
  # A new AAD app/service principal for CI (e.g. OIDC federated push) was
  # the cleaner option but is blocked by this tenant's policy (same
  # reason ci_identity.tf was abandoned); the registry's own built-in
  # admin account isn't an AAD app registration, so it isn't subject to
  # that block.
  admin_enabled = true
}

resource "azurerm_linux_web_app" "gateway" {
  name                = "app-${var.project_name}-${var.environment}-gateway"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    always_on = true

    health_check_path                 = "/healthz"
    health_check_eviction_time_in_min = 2

    # Pulled via this app's own managed identity (role assignment below),
    # not a registry username/password -- same pattern as the backend's
    # identity-based Storage/Key Vault access.
    container_registry_use_managed_identity = true

    application_stack {
      docker_image_name   = "gateway:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
    }
  }

  app_settings = {
    # nginx's envsubst entrypoint (built into nginx:alpine) substitutes
    # these into nginx.gateway.conf.template at container start.
    BACKEND_HOST  = azurerm_linux_web_app.backend.default_hostname
    FRONTEND_HOST = azurerm_linux_web_app.frontend.default_hostname

    # Custom container images don't get App Service's default port
    # guess; the image EXPOSEs 80, so this has to say so explicitly (same
    # kind of startup-probe mismatch the frontend's pm2 $PORT fix hit).
    WEBSITES_PORT = "80"
  }
}

resource "azurerm_role_assignment" "gateway_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_linux_web_app.gateway.identity[0].principal_id
}
