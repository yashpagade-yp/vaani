# ==============================================================
# Vaani Frontend — Dockerfile (Multi-Stage Build)
# ==============================================================
# Stage 1 (build):  Uses Node.js to install deps & build the app
# Stage 2 (serve):  Uses Nginx to serve the static files
#
# Why multi-stage? Node.js image is ~400MB, Nginx is ~25MB.
# We only need Node to BUILD, not to SERVE.
#
# Build:  docker build -t vaani-frontend .
# Run:    docker run -p 3000:80 vaani-frontend
# ==============================================================

# ══════════════════════════════════════════════════════════════
# STAGE 1: BUILD — Install dependencies and build production bundle
# ══════════════════════════════════════════════════════════════
FROM node:20-alpine AS build

WORKDIR /app

# ── Install dependencies (cached layer) ──────────────────────
# Copy package files first — Docker caches this layer.
# If your code changes but dependencies don't, npm ci is skipped!
COPY package.json package-lock.json ./
RUN npm ci

# ── Copy source code and build ────────────────────────────────
COPY . .
RUN npm run build

# ══════════════════════════════════════════════════════════════
# STAGE 2: SERVE — Lightweight Nginx server for static files
# ══════════════════════════════════════════════════════════════
FROM nginx:alpine

# ── Copy built files from Stage 1 ────────────────────────────
# Vite outputs to dist/ — copy that into Nginx's serving directory
COPY --from=build /app/dist /usr/share/nginx/html

# ── Copy custom Nginx config ─────────────────────────────────
# This handles SPA routing (sends all routes to index.html)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ── Expose port 80 (standard HTTP) ───────────────────────────
EXPOSE 80

# ── Start Nginx ──────────────────────────────────────────────
CMD ["nginx", "-g", "daemon off;"]
