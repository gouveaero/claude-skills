FROM oven/bun:1.1-slim

WORKDIR /app

COPY package.json bun.lock* ./
RUN bun install --frozen-lockfile || bun install

COPY server.ts ./

ENV PORT=3000
EXPOSE 3000

CMD ["bun", "run", "server.ts"]
