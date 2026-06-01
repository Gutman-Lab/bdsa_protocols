# BDSA Protocols – Frontend

Vite + React + TypeScript app for the BDSA Protocols platform (protocol management and documentation).

## Run in Docker

From the repo root:

- **Production**: `docker compose up -d` — frontend at http://localhost:3000
- **Dev (reload on change)**: from repo root run `./run-dev.sh` — Vite dev server with HMR at http://localhost:3001 (port 3001 to avoid conflict with 3000)

## Run locally

```bash
npm install
npm run dev
```

App at http://localhost:3000. For `bdsa-react-components` local linking, see the root README.

### Protocol UI (`/protocols`)

The protocols page uses **ProtocolManager** from `bdsa-react-components` (stain + region tabs, schema-driven forms). It persists to `GET/PUT /api/collections/{id}/protocols`.

**Local dependency:** `package.json` links `file:../../bdsa-react-components`. Before `npm run build` or Docker image build:

```bash
cd ../bdsa-react-components && npx vite build
cd ../bdsa_protocols/frontend && npm install
```

Optional env: `VITE_DEFAULT_COLLECTION_ID` to pre-select a collection. API calls use `VITE_API_URL` or the Vite/nginx `/api` proxy (see `vite.config.ts`).

## Build

```bash
npm run build
```

Output in `dist/`. The Docker image uses this and serves it with nginx.
