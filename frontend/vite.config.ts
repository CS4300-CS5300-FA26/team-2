import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: mirror the production proxy (server.mjs) so /api etc. hit local Django.
const target = process.env.API_ORIGIN || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: { "/api": target, "/admin": target, "/static": target, "/media": target },
  },
});
