# IRIS Agent Core
# Claude Agent SDK orchestrator

FROM node:20-slim AS base

RUN npm install -g pnpm

WORKDIR /app

# Install dependencies
FROM base AS deps

COPY pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY packages/agent-core/package.json packages/agent-core/
COPY packages/memory-service/package.json packages/memory-service/

RUN pnpm install --frozen-lockfile --filter @iris/agent-core...

# Build
FROM deps AS build

COPY packages/memory-service packages/memory-service/
COPY packages/agent-core packages/agent-core/
COPY tsconfig.json ./

RUN pnpm --filter @iris/memory-service build
RUN pnpm --filter @iris/agent-core build

# Production
FROM node:20-slim AS production

WORKDIR /app

# Copy built files and dependencies
COPY --from=build /app/packages/agent-core/dist /app/packages/agent-core/dist
COPY --from=build /app/packages/agent-core/package.json /app/packages/agent-core/
COPY --from=build /app/packages/memory-service/dist /app/packages/memory-service/dist
COPY --from=build /app/packages/memory-service/package.json /app/packages/memory-service/
COPY --from=build /app/node_modules /app/node_modules

# Create non-root user
RUN useradd -m -u 1000 iris && chown -R iris:iris /app
USER iris

# Data directory for SQLite
RUN mkdir -p /app/data
VOLUME /app/data

ENV NODE_ENV=production
ENV AGENT_API_PORT=3001

EXPOSE 3001

WORKDIR /app/packages/agent-core
CMD ["node", "dist/api-server.js"]
