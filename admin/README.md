# BDSA Protocols – Admin Panel

Read-only admin UI to inspect what’s stored in MongoDB via the backend API. One tab per resource: Collections, Protocols, Case ID Mappings, Patient ID Mappings, Slides, Block → Region.

## Run in Docker

From the repo root:

- **Production**: `docker compose up -d` — admin at http://localhost:3002  
- **Dev**: `./run-dev.sh` — admin at http://localhost:3002 with hot reload

## Run locally

```bash
cd admin && npm install && npm run dev
```

Open http://localhost:3002. Set `VITE_API_URL=http://localhost:8000` if the API is elsewhere.

## Usage

1. **Collections** tab lists all `collection_id` values.
2. Choose a collection in the dropdown (for all other tabs).
3. Switch tabs to view that resource’s data (JSON or table).

The app talks to the backend at the URL shown in the header (default `http://localhost:8000`).
