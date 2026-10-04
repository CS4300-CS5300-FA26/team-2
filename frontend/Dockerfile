FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

CMD ["sh", "-c", "npm run build && rm -rf /output/* && cp -r dist/* /output/"]
