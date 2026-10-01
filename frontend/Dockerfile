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
