FROM node:20-alpine AS builder

WORKDIR /app

ENV NODE_ENV=production

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps --no-optional

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage with Nginx
FROM nginx:1.27-alpine

# Copy nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/healthz || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]


