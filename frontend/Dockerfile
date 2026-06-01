# Production image (nginx). Build context: parent of bdsa_protocols (see docker-compose.yml).
FROM node:20-alpine AS components
WORKDIR /deps/bdsa-react-components
COPY bdsa-react-components/package.json bdsa-react-components/package-lock.json* ./
RUN npm install
COPY bdsa-react-components/ ./
RUN npx vite build

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=components /deps/bdsa-react-components /deps/bdsa-react-components
COPY bdsa_protocols/frontend/package.json bdsa_protocols/frontend/package-lock.json* ./
RUN npm install /deps/bdsa-react-components && npm install
COPY bdsa_protocols/frontend/index.html bdsa_protocols/frontend/vite.config.ts \
  bdsa_protocols/frontend/tsconfig.json bdsa_protocols/frontend/tsconfig.node.json ./
COPY bdsa_protocols/frontend/.eslintrc.cjs ./
COPY bdsa_protocols/frontend/src/ ./src/
COPY bdsa_protocols/frontend/public/ ./public/
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY bdsa_protocols/frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
