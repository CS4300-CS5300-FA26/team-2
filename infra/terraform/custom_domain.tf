# Apex (naked) domain on the gateway Web App (gateway.tf), not the
# frontend or backend directly -- the gateway is the single public
# origin both apps sit behind, same role the old Railway nginx container
# played before the AKS/App Service split.
#
# Azure requires the registrar's DNS to already resolve correctly before
# azurerm_app_service_custom_hostname_binding will apply: an ANAME (Name.com's
# ALIAS-equivalent) record at the apex pointing at this gateway app's
# default hostname, plus a TXT record at asuid.<domain> (value in
# output.frontend_domain_verification_id) proving ownership. ANAME over a
# plain A record on purpose: Basic tier's inbound IP is shared infra Azure
# can rotate without notice, and ANAME re-resolves to whatever that
# current IP is on every lookup instead of going stale.
#
# Set both at the registrar and wait for propagation
# (`dig path-finders.app` / `dig TXT asuid.path-finders.app`) before running
# `terraform apply` on this file. Moving this binding from the frontend app
# to the gateway app re-triggers domain verification -- the TXT value is
# per-app, so the ANAME target and TXT value both have to be updated to the
# gateway app's values, not reused from the frontend's old binding.

resource "azurerm_app_service_custom_hostname_binding" "gateway_apex" {
  hostname            = var.frontend_custom_domain
  app_service_name    = azurerm_linux_web_app.gateway.name
  resource_group_name = azurerm_resource_group.main.name
}

# Free App Service Managed Certificate -- only issues once the hostname
# binding above is verified, which itself only verifies once DNS is live.
resource "azurerm_app_service_managed_certificate" "gateway_apex" {
  custom_hostname_binding_id = azurerm_app_service_custom_hostname_binding.gateway_apex.id
}

resource "azurerm_app_service_certificate_binding" "gateway_apex" {
  hostname_binding_id = azurerm_app_service_custom_hostname_binding.gateway_apex.id
  certificate_id      = azurerm_app_service_managed_certificate.gateway_apex.id
  ssl_state           = "SniEnabled"
}

output "gateway_domain_verification_id" {
  description = "Set this as a TXT record at asuid.<domain> before applying this file."
  value       = azurerm_linux_web_app.gateway.custom_domain_verification_id
  sensitive   = true
}
