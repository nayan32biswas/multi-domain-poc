# Stage 1: Build the frontend
FROM node:22 AS builder

WORKDIR /app
COPY ./frontend .

RUN npm install && npm run build

# Final image to just copy to mounted volume (no CMD needed)
FROM nginx:alpine

COPY ./config/frontend-nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=builder /app/dist /usr/share/nginx/html
