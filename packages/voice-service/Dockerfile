# IRIS Voice Service (Node.js)
# WebSocket bridge for voice interaction

FROM node:20-slim AS base

RUN npm install -g pnpm

WORKDIR /app

# Install dependencies
FROM base AS deps

COPY pnpm-workspace.yaml pnpm-lock.yaml* ./
COPY packages/voice-service/package.json packages/voice-service/

RUN pnpm install --frozen-lockfile --filter @iris/voice-service

# Build
FROM deps AS build

COPY packages/voice-service packages/voice-service/
COPY tsconfig.json ./

RUN pnpm --filter @iris/voice-service build

# Production
FROM node:20-slim AS production

WORKDIR /app

# Copy built files and dependencies
COPY --from=build /app/packages/voice-service/dist /app/dist
COPY --from=build /app/packages/voice-service/package.json /app/
COPY --from=build /app/node_modules /app/node_modules

# Create non-root user
RUN useradd -m -u 1000 iris && chown -R iris:iris /app
USER iris

ENV NODE_ENV=production
ENV VOICE_WS_PORT=8002
ENV VOICE_BACKEND_URL=http://localhost:8001

EXPOSE 8002

CMD ["node", "dist/index.js"]
