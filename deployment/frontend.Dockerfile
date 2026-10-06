# Build the React app into static files that a web server can deliver
FROM node:20-slim AS frontend-build

# Set the working folder inside the temporary build container
WORKDIR /app

# Copy dependency information first so Docker can reuse this build layer
COPY frontend/package*.json ./

# Install the React project dependencies
RUN npm install

# Copy the React source code into the build container
COPY frontend/ ./

# Create the production files inside the dist folder
RUN npm run build


# Start a smaller container that only serves the finished website
FROM nginx:alpine

# Copy the Nginx configuration template used by Railway
COPY deployment/nginx.frontend.conf.template /etc/nginx/templates/default.conf.template

# Copy React's finished files into Nginx's public website folder
COPY --from=frontend-build /app/dist /usr/share/nginx/html

# Tell Railway that this container listens for web traffic on port 80
EXPOSE 80