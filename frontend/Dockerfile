FROM node:20-slim AS builder
WORKDIR /app
ARG NEXT_PUBLIC_API_BASE=http://localhost:8000
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/pages ./pages
COPY frontend/components ./components
COPY frontend/lib ./lib
COPY frontend/styles ./styles
COPY frontend/public ./public
COPY frontend/next.config.js frontend/tsconfig.json ./
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app ./
EXPOSE 3000
CMD ["npm", "start"]
