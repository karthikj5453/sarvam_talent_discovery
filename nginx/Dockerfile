# Stage 1: Build Frontend (Candidate Portal)
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
# Add dummy backend URL to build so it defaults to API proxy in prod
RUN echo "VITE_API_URL=/api" > .env
RUN npm run build

# Stage 2: Build Dashboard (HR Portal)
FROM node:20-alpine AS dashboard-builder
WORKDIR /app/dashboard
COPY dashboard/package*.json ./
RUN npm ci
COPY dashboard/ ./
RUN echo "VITE_API_URL=/api" > .env
RUN npm run build

# Stage 3: NGINX Server
FROM nginx:alpine
# Copy nginx config
COPY nginx/nginx.conf /etc/nginx/nginx.conf

# Copy built static files
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html/frontend
COPY --from=dashboard-builder /app/dashboard/dist /usr/share/nginx/html/dashboard

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
