# BDSA Protocols API

FastAPI backend for protocols, mappings, slides, block→region data, and BDSA JSON schemas.

## Base URLs

| Environment | API | Interactive docs |
|-------------|-----|------------------|
| Production | `https://api.bdsa.io` | `https://api.bdsa.io/docs` |
| Local (Docker) | `http://localhost:8000` | `http://localhost:8000/docs` |

The web UI at `https://schema.bdsa.io` proxies `/api` to the backend when using same-origin requests. **External servers and scripts should call `api.bdsa.io` directly.**

Full endpoint reference: Swagger at `/docs`, or see `backend/README.md`.

---

## API key (required for `/api/*` when enabled)

When `BDSA_API_KEY` is set in `.env`, every route under `/api/` requires a shared secret in the request header:

```http
X-API-Key: <your-secret>
```

### What needs the key

| Path | Key required? |
|------|----------------|
| `/api/**` | **Yes** (when `BDSA_API_KEY` is set) |
| `/health` | No |
| `/` | No |
| `/docs`, `/redoc` | No (use **Authorize** in Swagger to try `/api` calls) |

If `BDSA_API_KEY` is **unset**, `/api` accepts unauthenticated requests — intended for local dev only, not public hosts.

### Configuration (`.env`)

```bash
# Backend: enforces the key on /api routes
BDSA_API_KEY=your-long-random-secret

# Frontends (same value; sent automatically by the SPA)
VITE_BDSA_API_KEY=your-long-random-secret
```

Generate a new secret:

```bash
openssl rand -hex 24
```

After changing `.env`, recreate containers so they pick up the value:

```bash
docker compose up -d
```

### External server / script examples

**curl — list schemas**

```bash
export BDSA_API_KEY='your-secret'
curl -s -H "X-API-Key: $BDSA_API_KEY" \
  https://api.bdsa.io/api/schemas
```

**curl — list collections**

```bash
curl -s -H "X-API-Key: $BDSA_API_KEY" \
  https://api.bdsa.io/api/collections
```

**curl — get protocols for a collection**

```bash
curl -s -H "X-API-Key: $BDSA_API_KEY" \
  "https://api.bdsa.io/api/collections/my-collection-id/protocols"
```

**curl — replace protocols (PUT)**

```bash
curl -X PUT \
  -H "X-API-Key: $BDSA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "stainProtocols": [],
    "regionProtocols": [],
    "blockProtocols": [],
    "source": "my-external-tool",
    "version": "1.0"
  }' \
  "https://api.bdsa.io/api/collections/my-collection-id/protocols"
```

**Python**

```python
import os
import requests

API = "https://api.bdsa.io"
KEY = os.environ["BDSA_API_KEY"]
HEADERS = {"X-API-Key": KEY}

r = requests.get(f"{API}/api/schemas", headers=HEADERS, timeout=30)
r.raise_for_status()
print(r.json())

r = requests.get(f"{API}/api/collections", headers=HEADERS, timeout=30)
r.raise_for_status()
print(r.json())
```

### Swagger UI

1. Open `https://api.bdsa.io/docs`
2. Click **Authorize**
3. Enter the same value as `BDSA_API_KEY` for `X-API-Key`
4. Use **Try it out** on any endpoint

---

## Common endpoints (quick reference)

| Resource | GET | PUT |
|----------|-----|-----|
| BDSA JSON schemas | `/api/schemas`, `/api/schemas/{id}`, `/api/schemas/combined` | — |
| Collections | `/api/collections` | `/api/collections/{id}/metadata` |
| Protocols | `/api/collections/{id}/protocols` | same path |
| Case ID mappings | `/api/collections/{id}/case-id-mappings` | same path (+ merge, validate, allocate) |
| Patient ID mappings | `/api/collections/{id}/patient-id-mappings` | same path |
| Slides | `/api/collections/{id}/slides` | same path |
| Block→region | `/api/collections/{id}/block2region` | `/api/collections/{id}/cases/{case_id}/block2region` |

Schema download as attachment: `GET /api/schemas/clinical?download=true`

See `backend/README.md` for merge routes, versioning, DSA sync, and admin backup.

### Case ID mappings (localCaseId → bdsaCaseId)

Per-collection registry used by pub-data sync (`bdsa-pub-data`). Format: `BDSA-{institutionId3}-{sequence5}` (e.g. `BDSA-002-00001` for U. Kentucky / `institutionId` `002`).

Each mapping row may include optional **`alternateIds`** — a map of external identifier systems to values (e.g. NACC case IDs). System keys are lowercase (`nacc`, `ndd`, …). Within a collection, each `(system, value)` pair must map to exactly one `localCaseId`. JSON schema: `GET /api/schemas/case-id-mappings`.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/collections/{id}/case-id-mappings` | Read all mappings |
| PUT | `/api/collections/{id}/case-id-mappings` | Full replace (validates 1:1 within payload) |
| POST | `/api/collections/{id}/case-id-mappings/merge` | Merge by `localCaseId` (409 on conflict) |
| POST | `/api/collections/{id}/case-id-mappings/validate` | Dry-run merge validation |
| POST | `/api/collections/{id}/case-id-mappings/allocate` | Atomically assign next free `bdsaCaseId` |
| POST | `/api/collections/{id}/case-id-mappings/allocate-batch` | Allocate many locals in one request |
| GET | `/api/collections/{id}/case-id-mappings/by-bdsa/{bdsaCaseId}` | Lookup one mapping |
| GET | `/api/collections/{id}/case-id-mappings/by-local/{localCaseId}` | Lookup one mapping |
| GET | `/api/collections/{id}/case-id-mappings/by-alternate/{system}/{value}` | Lookup by external ID (e.g. `nacc/U1234567`) |

**Merge `alternateIds`:** idempotent when the same value is re-posted. Returns **409** (`duplicate_alternate_id`) if a system value is already bound to a different `localCaseId`. You may merge alternate IDs alone on an existing case (no `bdsaCaseId` in the row).

**Example — attach NACC ID to an existing case:**

```bash
curl -X POST -H "X-API-Key: $BDSA_API_KEY" -H "Content-Type: application/json" \
  -d '{"institutionId":"002","mappings":[{"localCaseId":"R1290","alternateIds":{"nacc":"U1234567"}}],"source":"manual"}' \
  "https://api.bdsa.io/api/collections/kentucky/case-id-mappings/merge"
```

### Region label mappings (REGIONO → regionProtocolId)

Per-collection crosswalk for UK `REGIONO` free text → `regionProtocolId`. Labels are normalized server-side (NFKD, lowercase, alphanumeric tokens).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/collections/{id}/region-label-mappings` | Read all mappings |
| PUT | `/api/collections/{id}/region-label-mappings` | Full replace |
| POST | `/api/collections/{id}/region-label-mappings/merge` | Merge by `normalized` label |
| POST | `/api/collections/{id}/region-label-mappings/validate` | Dry-run validation |
| GET | `/api/collections/{id}/region-label-mappings/by-label/{normalized}` | Lookup validated mapping |

**Rules:** one `normalized` label → one `regionProtocolId`; `regionProtocolId` must exist in collection `regionProtocols` (**422** if unknown). Lookup returns **404** for unmapped or `validated: false` rows.

Each mapping row includes **`sourceField`** — the CSV column the text came from (default `"REGIONO"`). Also stored: `regionLabel` (original text), `normalized`, `validated`, and `source` (sync tool name).

### Stain label mappings (STAINO → stainProtocolId)

Per-collection crosswalk for UK `STAINO` free text → `stainProtocolId` (e.g. `PHF-1` → `kentucky_tau`, `Nab228` → `kentucky_abeta`). Numeric `STAIN` codes 1–5 map directly to protocols; this registry covers overrides and non-standard aliases.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/collections/{id}/stain-label-mappings` | Read all mappings |
| PUT | `/api/collections/{id}/stain-label-mappings` | Full replace |
| POST | `/api/collections/{id}/stain-label-mappings/merge` | Merge by `normalized` label |
| POST | `/api/collections/{id}/stain-label-mappings/validate` | Dry-run validation |
| GET | `/api/collections/{id}/stain-label-mappings/by-label/{normalized}` | Lookup validated mapping |

**Rules:** same as region label mappings — one `normalized` label → one `stainProtocolId`; protocol must exist in collection `stainProtocols`; lookup excludes `validated: false` rows. Each row includes **`sourceField`** (default `"STAINO"`) for the originating CSV column.

**Example:**

```bash
# Register PHF-1 -> kentucky_tau
curl -X POST -H "X-API-Key: $BDSA_API_KEY" -H "Content-Type: application/json" \
  -d '{"mappings":[{"stainLabel":"PHF-1","sourceField":"STAINO","stainProtocolId":"kentucky_tau","validated":true}],"source":"sync_search_data"}' \
  "https://api.bdsa.io/api/collections/kentucky/stain-label-mappings/merge"

# Check if a term is mapped
curl -H "X-API-Key: $BDSA_API_KEY" \
  "https://api.bdsa.io/api/collections/kentucky/stain-label-mappings/by-label/phf%201"
```

**Merge rules:** idempotent when the same `localCaseId` + `bdsaCaseId` pair is posted again. Returns **409** if `localCaseId` is reassigned to a different `bdsaCaseId`, or if `bdsaCaseId` is already used by another `localCaseId`.

**Allocate example:**

```bash
curl -X POST -H "X-API-Key: $BDSA_API_KEY" -H "Content-Type: application/json" \
  -d '{"localCaseId":"R1290","institutionId":"002","source":"sync_search_data"}' \
  "https://api.bdsa.io/api/collections/kentucky/case-id-mappings/allocate"
```

---

## Security notes

- The API key **blocks casual abuse** (scanners, drive-by POSTs). It is **not** hidden from browser users — anyone using the public SPA can see `VITE_BDSA_API_KEY` in network traffic or the built JS bundle.
- Keep `BDSA_API_KEY` out of git. Only `.env` on the server (never commit it).
- Optional extra layer: restrict `api.bdsa.io` in Nginx Proxy Manager by IP allowlist for known servers only.
- DSA credentials (`DSA_API_URL`, `DSA_API_KEY`) are separate and used only by the backend for Girder sync.

---

## Related docs

- `backend/README.md` — full backend route list and MongoDB details
- `docs/CURSOR_INTEGRATION.md` — bdsa-react-components integration
- `frontend/public/schemas/README.md` — refreshing Pitt schema JSON files
