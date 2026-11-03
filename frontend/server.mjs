// Production server for the Azure web app: serves dist/ with SPA history fallback and
// reverse-proxies backend paths to the Django API, so the browser sees ONE origin
// (no CORS; session/CSRF cookies just work). Zero dependencies.
import http from "node:http";
import https from "node:https";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const dist = path.join(path.dirname(fileURLToPath(import.meta.url)), "dist");
const api = new URL(process.env.API_ORIGIN || "https://app-pathfinder-prod-api.azurewebsites.net");
// ponytail: prefix list; Django JSON endpoints must live under one of these (keep SPA routes off them).
const proxied = (process.env.PROXY_PREFIXES || "/api/,/admin/,/static/,/media/").split(",");
const types = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml",
  ".png": "image/png", ".jpg": "image/jpeg", ".ico": "image/x-icon", ".json": "application/json",
  ".woff2": "font/woff2", ".map": "application/json" };

function proxy(req, res) {
  // Azure routes by Host, so send the API's host and pass the public one as X-Forwarded-Host.
  const headers = { ...req.headers, host: api.host, "x-forwarded-host": req.headers.host, "x-forwarded-proto": "https" };
  const up = (api.protocol === "https:" ? https : http).request(
    { host: api.hostname, port: api.port || undefined, path: req.url, method: req.method, headers },
    (r) => { res.writeHead(r.statusCode, r.headers); r.pipe(res); });
  up.on("error", () => { res.writeHead(502); res.end("Bad gateway"); });
  req.pipe(up);
}

http.createServer((req, res) => {
  const { pathname } = new URL(req.url, "http://x");
  if (proxied.some((p) => pathname.startsWith(p) || pathname + "/" === p)) return proxy(req, res);
  let file = path.join(dist, path.normalize(decodeURIComponent(pathname)));
  if (!file.startsWith(dist) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    // missing asset -> 404; anything else is a client-side route -> index.html
    if (path.extname(pathname)) { res.writeHead(404); return res.end("Not found"); }
    file = path.join(dist, "index.html");
  }
  res.writeHead(200, {
    "content-type": types[path.extname(file)] || "application/octet-stream",
    "cache-control": pathname.startsWith("/assets/") ? "public, max-age=31536000, immutable" : "no-cache",
  });
  fs.createReadStream(file).pipe(res);
}).listen(process.env.PORT || 8080);
