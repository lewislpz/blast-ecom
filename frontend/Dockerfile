FROM node:24.21.0-bookworm-slim AS development
ENV NODE_ENV=development
WORKDIR /app
RUN chown node:node /app
COPY --chown=node:node frontend/package.json frontend/package-lock.json ./
USER node
RUN npm ci
COPY --chown=node:node frontend/ ./
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM node:24.21.0-bookworm-slim AS production-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginxinc/nginx-unprivileged:1.29.4-alpine AS production
USER root
RUN apk upgrade --no-cache
USER 101
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=production-build /app/dist/ /usr/share/nginx/html/
EXPOSE 8080
