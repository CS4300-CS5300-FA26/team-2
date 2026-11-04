# App Service replaces AKS/SWA (see the ADR update): both the Django API
# and the React static build deploy here as plain source, not a container
# -- backend's via Oryx build, frontend's pre-built in CI (see deploy.yml;
# Oryx's own build OOMs on this plan's B1 tier). backend/Dockerfile and
# frontend/Dockerfile stay for local docker-compose dev only. The gateway
# Web App (gateway.tf) in front of both is the one container-based
# exception -- it's a thin nginx reverse proxy, not an app to Oryx-build.

resource "azurerm_service_plan" "main" {
  name                = "asp-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"

  # Basic B1 (~$13.14/mo): cheapest tier with always_on, which the 24/7
  # uptime target requires. worker_count is the App Service Plan's
  # instance count; it's per-plan, not per-app, so both Web Apps below
  # share these 2 instances.
  sku_name     = "B1"
  worker_count = 2
}

resource "azurerm_linux_web_app" "backend" {
  name                = "app-${var.project_name}-${var.environment}-api"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  # PR #53 review: reject plain HTTP instead of silently serving it.
  https_only = true

  # VNet Integration via the delegated subnet in network.tf, so outbound
  # traffic from Django can reach the private Postgres server, Key Vault,
  # and Storage over the VNet instead of the public internet.
  virtual_network_subnet_id = azurerm_subnet.app_service.id

  identity {
    type = "SystemAssigned"
  }

  site_config {
    # Required for the health check below and for a 24/7 uptime target;
    # only available Basic tier and up (B1, already selected above).
    always_on = true

    # Route ALL outbound traffic through the VNet integration, not just
    # RFC1918 ranges, so calls to Key Vault/Storage's public endpoints
    # (gated by VNet-scoped network ACLs, see keyvault.tf/storage.tf) use
    # the VNet path too, not just Postgres's private IP.
    vnet_route_all_enabled = true

    health_check_path                 = "/healthz/"
    health_check_eviction_time_in_min = 2

    application_stack {
      # Matches backend/requirements.txt's Django 5.1 (requires Python
      # 3.10+); 3.12 matches backend/Dockerfile's base image.
      python_version = "3.12"
    }

    # Oryx's default Python startup guesses at an entrypoint; pin the
    # real one. Unlike backend/entrypoint.sh (Docker-only), migrate runs
    # inline here -- there's no separate deploy-time hook in the App
    # Service source-deploy path, so startup is the only place left.
    # worker_count=2 means both instances can race this on a simultaneous
    # cold start; Django migrations aren't lock-protected against that,
    # but at this scale (small, infrequent deploys) the risk is accepted
    # rather than engineered around.
    app_command_line = "python manage.py migrate --noinput && gunicorn pathfinder.wsgi:application --bind=0.0.0.0:8000"
  }

  app_settings = {
    # Oryx build on source deploy; without this a zip/source deploy just
    # copies files instead of running pip install.
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
    DJANGO_SETTINGS_MODULE         = "pathfinder.settings.prod"

    # App Service's native Key Vault reference syntax: resolved at
    # runtime using the Web App's own identity (SystemAssigned above),
    # which keyvault.tf grants Key Vault Secrets User. Not the CSI driver
    # pattern, that was AKS-specific.
    SECRET_KEY   = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=SECRET-KEY)"
    DATABASE_URL = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=DATABASE-URL)"

    # prod.py only calls sentry_sdk.init() if this is non-empty, so this
    # is a no-op until the secret below is actually set.
    SENTRY_DSN = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=SENTRY-DSN)"

    # Media storage account/container for prod.py's AzureStorage backend.
    # Not secrets (auth is managed identity, not a key), so plain app
    # settings rather than Key Vault references.
    AZURE_STORAGE_ACCOUNT_NAME = azurerm_storage_account.media.name
    AZURE_STORAGE_CONTAINER    = azurerm_storage_container.media.name

    # prod.py's Django security settings: without these the app 500s on
    # every request (DisallowedHost) or rejects admin/API POSTs (CSRF).
    # Built from the name below rather than self-referencing
    # default_hostname (Terraform forbids a resource referring to
    # itself). ALLOWED_HOSTS is just this app's own Host header, so it
    # never needs the frontend's domain; CSRF_TRUSTED_ORIGINS does,
    # since that's the cross-origin caller's Origin once the frontend
    # moves off azurewebsites.net (custom_domain.tf).
    ALLOWED_HOSTS = "app-${var.project_name}-${var.environment}-api.azurewebsites.net"

    # PR #53 review: also needs the frontend's own azurewebsites.net
    # hostname, not just the custom domain -- direct testing against
    # that URL (bypassing the gateway) 403s on any POST without it.
    CSRF_TRUSTED_ORIGINS = "https://app-${var.project_name}-${var.environment}-api.azurewebsites.net,https://app-${var.project_name}-${var.environment}-web.azurewebsites.net,https://${var.frontend_custom_domain}"

    # Separate origins, no shared gateway in this deploy -- the frontend's
    # fetch calls need CORS to even reach this API. Covers both the custom
    # domain and the frontend's own azurewebsites.net hostname (useful if
    # the domain is ever unbound/changed).
    CORS_ALLOWED_ORIGINS = "https://${var.frontend_custom_domain},https://app-${var.project_name}-${var.environment}-web.azurewebsites.net"

    # Oryx auto-runs `manage.py collectstatic` when manage.py sits at the
    # deploy root, which it should here, but that depends on however the
    # (not-yet-written) deploy workflow packages this repo. Explicit and
    # idempotent, so it's cheap insurance either way.
    POST_BUILD_COMMAND = "python manage.py collectstatic --noinput"
  }
}

resource "azurerm_linux_web_app" "frontend" {
  name                = "app-${var.project_name}-${var.environment}-web"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  service_plan_id     = azurerm_service_plan.main.id

  # PR #53 review: reject plain HTTP instead of silently serving it.
  https_only = true

  site_config {
    always_on = true

    application_stack {
      # Node is only needed as the Oryx build runtime (tsc -b && vite
      # build, per frontend/package.json); the result is static files.
      node_version = "20-lts"
    }

    # frontend/package.json's build script is "tsc -b && vite build",
    # and Vite's default output directory is "dist" (not overridden in
    # vite.config). pm2 is bundled in App Service's Node Linux image;
    # this is Microsoft's documented pattern for serving a static SPA
    # build without adding a dependency for it.
    #
    # App Service's startup probe checks port 8080 ($PORT) specifically;
    # pm2 serve without an explicit port picks its own default, so the
    # probe sees nothing listening and kills the container after 230s
    # ("No listening ports were detected") even though pm2 is actually up.
    app_command_line = "pm2 serve /home/site/wwwroot/dist $PORT --no-daemon --spa"
  }

  app_settings = {
    # false: deploy.yml builds the frontend in the GitHub Actions runner
    # and ships the pre-built dist/ output, not raw source. B1's 1 core/
    # 1.75GB can't reliably run `npm install` + `tsc -b && vite build`
    # itself -- confirmed live, Oryx's own build silently OOM-killed mid
    # `npm install` with no error logged, just a generic failure after
    # Kudu's watchdog gave up. With this false, Kudu does a plain file
    # copy into wwwroot instead of invoking Oryx.
    SCM_DO_BUILD_DURING_DEPLOYMENT = "false"

    # No VITE_API_BASE_URL app setting here: Vite inlines import.meta.env.VITE_*
    # at build time, and that build now happens in deploy.yml's GitHub Actions
    # runner (see SCM_DO_BUILD_DURING_DEPLOYMENT above), not in an Oryx build
    # container on this Web App -- an App Setting here would never be read.
    # deploy.yml sets the same value directly as a build step env var instead.
  }
}
