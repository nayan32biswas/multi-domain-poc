# Stage 1: Build the frontend
FROM node:22 AS builder

WORKDIR /app
COPY . .

RUN npm install && npm run build

# Final image to just copy to mounted volume (no CMD needed)
FROM alpine:3.22

WORKDIR /output
COPY --from=builder /app/dist ./
