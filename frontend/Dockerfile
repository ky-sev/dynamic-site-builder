FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build
RUN npm prune --omit=dev --legacy-peer-deps

FROM node:22-alpine AS runtime

ENV NODE_ENV=production
ENV PORT=4000
WORKDIR /app

COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/dist/json-site ./dist/json-site
COPY --chown=node:node package.json ./package.json

USER node
EXPOSE 4000

CMD ["node", "dist/json-site/server/server.mjs"]
