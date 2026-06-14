import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The backend URL is read from VITE_API_BASE at build/runtime; in dev we proxy
// /api to the local FastAPI server so the app works from a single origin.
export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET || "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
