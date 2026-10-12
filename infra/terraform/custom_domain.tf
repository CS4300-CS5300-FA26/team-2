# Apex (naked) domain on the frontend Web App only; the backend API stays on
# its azurewebsites.net hostname (app_service.tf's ALLOWED_HOSTS/
# CSRF_TRUSTED_ORIGINS reflect that split).
#
# Azure requires the registrar's DNS to already resolve correctly before
# azurerm_app_service_custom_hostname_binding will apply: an ANAME (Name.com's
# ALIAS-equivalent) record at the apex pointing at
# app-pathfinder-prod-web.azurewebsites.net, plus a TXT record at
# asuid.<domain> (value in output.frontend_domain_verification_id) proving
# ownership. ANAME over a plain A record on purpose: Basic tier's inbound IP
# is shared infra Azure can rotate without notice, and ANAME re-resolves to
# whatever that current IP is on every lookup instead of going stale.
#
# Set both at the registrar and wait for propagation
# (`dig path-finders.app` / `dig TXT asuid.path-finders.app`) before running
# `terraform apply` on this file.

resource "azurerm_app_service_custom_hostname_binding" "frontend_apex" {
  hostname            = var.frontend_custom_domain
  app_service_name    = azurerm_linux_web_app.frontend.name
  resource_group_name = azurerm_resource_group.main.name
}

# Free App Service Managed Certificate -- only issues once the hostname
# binding above is verified, which itself only verifies once DNS is live.
resource "azurerm_app_service_managed_certificate" "frontend_apex" {
  custom_hostname_binding_id = azurerm_app_service_custom_hostname_binding.frontend_apex.id
}

resource "azurerm_app_service_certificate_binding" "frontend_apex" {
  hostname_binding_id = azurerm_app_service_custom_hostname_binding.frontend_apex.id
  certificate_id      = azurerm_app_service_managed_certificate.frontend_apex.id
  ssl_state           = "SniEnabled"
}

output "frontend_domain_verification_id" {
  description = "Set this as a TXT record at asuid.<domain> before applying this file."
  value       = azurerm_linux_web_app.frontend.custom_domain_verification_id
  sensitive   = true
}
