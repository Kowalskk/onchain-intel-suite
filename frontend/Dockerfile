# Build environment
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production server (for static Vite build)
FROM nginx:alpine
# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html
# Custom Nginx config to fallback to index.html for SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
