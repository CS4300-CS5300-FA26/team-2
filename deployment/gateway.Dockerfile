# Reverse proxy giving the frontend and backend App Services one public
# origin (infra/terraform/gateway.tf). Pure nginx -- the frontend App
# Service already builds and serves the React SPA itself, so unlike the
# old Railway setup this image doesn't bundle a Node build stage.
FROM nginx:alpine

COPY deployment/nginx.gateway.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 80
