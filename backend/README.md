# BDSA Protocols Backend

FastAPI + MongoDB backend for storing **region protocols**, **stain protocols**, **case ID mappings**, and **slide (stain) metadata**. Designed as the canonical server for [BDSA-Schema-Wrangler](https://github.com/BDSA/BDSA-Schema-Wrangler); wrangler can push/pull from this API instead of (or in addition to) DSA folder metadata.

**Everything runs in Docker** via the root `docker-compose.yml`.

## Run (Docker only)

From the **repo root**:

```bash
docker compose up -d
```

- **API**: http://localhost:8000  
- **Docs**: http://localhost:8000/docs  
- **MongoDB**: localhost:27017 (for tools if needed)

### API key (recommended for public hosts)

Set `BDSA_API_KEY` in `.env`. Most `/api/*` routes then require header:

```http
X-API-Key: your-secret-here
```

`/api/schemas` (list + GET) stays public. `/`, `/health`, and `/docs` stay open (use **Authorize** in Swagger with the same key to try endpoints). If `BDSA_API_KEY` is unset, `/api` accepts unauthenticated requests (local dev only).

Frontends send the key via `VITE_BDSA_API_KEY` (same value as `BDSA_API_KEY`).

```bash
curl -H "X-API-Key: $BDSA_API_KEY" http://localhost:8000/api/schemas
```

Full details (external servers, Python examples, env vars): **`docs/API.md`**.

### NACC clinical data

`GET /api/clinical/by-nacc/{naccid}` serves clinical-schema fields loaded from the investigator NACC dump. Import (gitignored CSV):

```bash
docker compose run --rm \
  -v "$(pwd)/docs:/data:ro" -v "$(pwd)/scripts:/scripts:ro" \
  backend python /scripts/import_nacc_clinical.py \
  --csv /data/investigator_nacc74.csv \
  --mongodb-url mongodb://mongodb:27017 \
  --mongodb-db bdsa_protocols
```

Rebuild after code changes:

```bash
docker compose up -d --build
```

## API Overview

All collection-scoped resources use `collection_id` in the path (e.g. DSA folder id or a custom id like `"1"`).

| Resource | GET | PUT | POST (merge) |
|----------|-----|-----|--------------|
| **Protocols** | `/api/collections/{id}/protocols` | Replace | `/api/collections/{id}/protocols/merge` |
| **Case ID mappings** | `/api/collections/{id}/case-id-mappings` | Replace | `/api/collections/{id}/case-id-mappings/merge` (+ `/validate`, `/allocate`, `/allocate-batch`, `/by-bdsa/{id}`, `/by-local/{id}`) |
| **Region label mappings** | `/api/collections/{id}/region-label-mappings` | Replace | `/api/collections/{id}/region-label-mappings/merge` (+ `/validate`, `/by-label/{normalized}`) |
| **Stain label mappings** | `/api/collections/{id}/stain-label-mappings` | Replace | `/api/collections/{id}/stain-label-mappings/merge` (+ `/validate`, `/by-label/{normalized}`) |
| **Patient ID mappings** | `/api/collections/{id}/patient-id-mappings` | Replace | `/api/collections/{id}/patient-id-mappings/merge` |
| **Slides** | `/api/collections/{id}/slides` | Replace | - |
| **Block→region (one case)** | `/api/collections/{id}/cases/{case_id}/block2region` | Replace | - |
| **Block→region (all cases)** | `/api/collections/{id}/block2region` | - | - |
| **Collections for case** | `GET /api/collections/cases/{case_id}/collections` | - | - |
| **Cases in collection** | `GET /api/collections/{id}/cases` | - | - |

### BDSA JSON schemas (static, no MongoDB)

Pitt split schemas live in `app/data/schemas/`. Refresh from upstream with the script in `frontend/public/schemas/README.md`, then copy JSON into `backend/app/data/schemas/`.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/schemas` | List schema ids + metadata |
| `GET /api/schemas/{id}` | One schema (`clinical`, `region`, `stain`, `slide`) |
| `GET /api/schemas/{id}?download=true` | Same, as attachment |
| `GET /api/schemas/combined` | All four merged for flattened/CDE views |

- **Patient ID mappings**: store `localPatientId` with optional `bdsaPatientId` (BDSA-Patient-ID key); GET supports `?localPatientId=xyz` to look up one.
- **Block2region**: store/retrieve a `blockId → regionId` map per case (case_id can be local or BDSA case id). Each case document can include **mapping_source** (e.g. `"LLM"`, `"manual"`, `"import"`) and **validated** (boolean). PUT body example: `{ "block2region": { "blockA": "region1", "blockB": "region2" }, "mapping_source": "LLM", "validated": false }`. When you **PUT** block2region for a case, the backend (1) saves a **versioned snapshot** in `block2region_versions` (each PUT = new version), (2) updates the current doc, (3) ensures the case is in **case-id-mappings** and **case_collection_registry**. **Versioning**: `GET .../cases/{case_id}/block2region/versions` lists versions (newest first); `POST .../cases/{case_id}/block2region/restore` with body `{ "version": N }` restores that version (and creates a new version entry).
- **List collections**: `GET /api/collections` → `{ "collection_ids": ["..."] }`
- **Rename collection**: `PUT /api/collections/{id}/rename` body `{ "new_collection_id": "..." }` — updates the ID across all resources.
- **Delete collection**: `DELETE /api/collections/{id}?confirm=true` — permanently deletes all data for that collection (protocols, mappings, slides, block2region, versions, registry). Requires `confirm=true`.
- **Collections for case**: `GET /api/collections/cases/{case_id}/collections` → `{ "case_id": "...", "collection_ids": ["..."] }`
- **Cases in collection**: `GET /api/collections/{collection_id}/cases` → `{ "collection_id": "...", "case_ids": ["..."] }`
- **Health**: `GET /health` → `{ "status": "ok" }`
- **Admin backup** (full Mongo JSON export): `GET /api/admin/backup` (download); `POST /api/admin/backup/save` writes under `BDSA_BACKUP_DIR` when set. The **admin UI** header includes **Download backup**; with dev compose, files also land in repo `backups/`.

Request/response shapes match the wrangler’s DSA folder metadata format (e.g. `stainProtocols`, `regionProtocols`, `bdsaCaseIdMappings.mappings`, etc.) so the wrangler can swap in this server as the canonical source with minimal changes.
