# BDSA Schema API — integration handoff for `bdsa-pub-data`

Send this document to the agent working on **bdsa_protocols** / **schema.bdsa.io** when adding API functionality needed by the pub-data sync tooling.

**Consumer repo:** `bdsa-pub-data`  
**Client code:** `sync_search_data/` (Python; Girder + schema API)  
**Existing API reference:** [schema_api.md](./schema_api.md)

---

## 1. What we are building

We are publishing UK neuropathology data to **pub-data** (Girder) and registering it in the **BDSA Protocols** schema store so slides/cases use consistent BDSA metadata.

| Layer | System | Role |
|-------|--------|------|
| Thumbnails + folders | `pub-data.bdsa.io` Girder | One folder per local patient ID (`R1290`, …) |
| Slide metadata | `item.meta.uk` + `item.meta.bdsa` | Per-slide stain/region from CSV |
| Case ID registry | `api.bdsa.io` | Maps `localCaseId` → `bdsaCaseId` |
| Region label registry | `api.bdsa.io` | Maps `REGIONO` text → `regionProtocolId` (**P2 — §8**) |
| Protocol definitions | `api.bdsa.io` collection `kentucky` | Stain/region protocols (U. Kentucky, #2) |

**Scripts (consumer side):**

| Script | Purpose |
|--------|---------|
| `sync_search_data/sync_uk_item_metadata.py` | Push per-slide metadata to Girder items |
| `sync_search_data/sync_uk_case_id_mappings.py` | Assign BDSA case IDs to patient folders |
| `sync_search_data/sync_uk_regiono_mappings.py` | Register REGIONO text → region protocol (upstream + local registry) |
| `sync_search_data/audit_uk_protocols.py` | Audit CSV stain/region coverage vs kentucky protocols |
| `sync_search_data/schema_client.py` | HTTP client for schema API |
| `sync_search_data/case_id_registry.py` | Local JSON registry + validation helpers (case IDs) |
| `sync_search_data/regiono_protocol_registry.py` | Local JSON registry + validation helpers (REGIONO labels) |
| `sync_search_data/registries/kentucky_case_id_mappings.json` | Local audit trail — case IDs (git-tracked) |
| `sync_search_data/registries/kentucky_regiono_protocol_mappings.json` | Local audit trail — REGIONO labels (git-tracked) |

**Auth:** `X-API-Key` header (`SCHEMA_BDSA_API_KEY` or `BDSA_API_KEY` in `.env`). See [schema_api.md](./schema_api.md).

---

## 2. Collections in use

| UI label | API `collection_id` | Institution # | `institutionId` in payloads |
|----------|---------------------|---------------|-----------------------------|
| U. Kentucky | `kentucky` | 2 | `002` |

List collections: `GET /api/collections`

```json
{
  "collections": [
    { "collection_id": "kentucky", "display_name": "U. Kentucky", "number": 2 }
  ]
}
```

---

## 3. Case ID mapping — current contract

### Endpoints (already exist)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/collections/{collection_id}/case-id-mappings` | Read all mappings |
| PUT | `/api/collections/{collection_id}/case-id-mappings` | Full replace |
| POST | `/api/collections/{collection_id}/case-id-mappings/merge` | Merge by `localCaseId` |

OpenAPI schemas: `CaseIdMappingItem`, `CaseIdMappingsPayload`, `CaseIdMappingsResponse`.

### Payload shape

**Request / stored document (`CaseIdMappingsPayload`):**

```json
{
  "institutionId": "002",
  "mappings": [
    { "localCaseId": "R1290", "bdsaCaseId": "BDSA-002-00001" },
    { "localCaseId": "R1291", "bdsaCaseId": "BDSA-002-00002" }
  ],
  "source": "sync_search_data",
  "version": "1.0",
  "totalMappings": 2,
  "lastUpdated": "2026-06-08T21:00:00Z"
}
```

**GET response:**

```json
{
  "success": true,
  "collection_id": "kentucky",
  "caseIdMappings": { ... CaseIdMappingsPayload or null ... }
}
```

### BDSA case ID format (consumer convention)

```
BDSA-{institutionId3}-{sequence5}
```

Examples: `BDSA-002-00001`, `BDSA-002-00014`

- `institutionId3` = zero-padded collection number (`kentucky` → `002`)
- `sequence5` = zero-padded sequential integer, unique **within that institution/collection**

### Invariants we must enforce

1. **One `localCaseId` → one `bdsaCaseId`** (per collection).  
   Example: `R1290` must never map to both `BDSA-002-00001` and `BDSA-002-00009`.

2. **One `bdsaCaseId` → one `localCaseId`** (per collection).  
   Example: `BDSA-002-00002` must not be assigned to both `R1291` and `R1292`.

3. **Allocations must be unique upstream** before write.  
   Consumer queries `GET case-id-mappings` before assigning and again immediately before `merge`.

---

## 4. Observed behavior (2026-06-08) — please fix

These were verified against production `api.bdsa.io`:

### 4.1 Merge silently overwrites existing `localCaseId`

If `R1290 → BDSA-002-00001` exists, posting merge with `R1290 → BDSA-002-99999` **succeeds** and replaces the mapping with no error.

**Expected:** HTTP **409 Conflict** with a clear error body (see §5.1).

### 4.2 Duplicate `bdsaCaseId` allowed

Merge accepts two rows with the same `bdsaCaseId` for different `localCaseId` values (e.g. both `R1291` and `R1292 → BDSA-002-00002`).

**Expected:** HTTP **409 Conflict** (see §5.2).

### 4.3 No server-side allocate / validate

Consumer must scan all mappings client-side to find the next free ID. Works, but race-prone if multiple writers run concurrently.

---

## 5. Feature requests (priority order)

### P0 — Validation on PUT and merge (breaking-safe)

Add validation to:

- `PUT /api/collections/{collection_id}/case-id-mappings`
- `POST /api/collections/{collection_id}/case-id-mappings/merge`

#### 5.1 Reject reassignment of `localCaseId`

When merging `{ localCaseId, bdsaCaseId }`:

- If `localCaseId` **already exists** with a **different** `bdsaCaseId` → **409**

```json
{
  "detail": "localCaseId already mapped",
  "conflict": {
    "kind": "local_case_reassigned",
    "localCaseId": "R1290",
    "existingBdsaCaseId": "BDSA-002-00001",
    "requestedBdsaCaseId": "BDSA-002-99999"
  }
}
```

**Allowed:** merge is idempotent when the same pair is posted again (same `localCaseId` + same `bdsaCaseId`).

#### 5.2 Reject duplicate `bdsaCaseId`

When adding/updating any mapping:

- If `bdsaCaseId` is already used by a **different** `localCaseId` → **409**

```json
{
  "detail": "bdsaCaseId already assigned",
  "conflict": {
    "kind": "duplicate_bdsa_case_id",
    "bdsaCaseId": "BDSA-002-00002",
    "existingLocalCaseId": "R1291",
    "requestedLocalCaseId": "R1292"
  }
}
```

#### 5.3 Full PUT must also validate the entire payload

PUT replace should reject the whole request if **any** row violates 5.1 or 5.2 (not only on merge).

---

### P1 — Allocate next case ID (atomic)

**New endpoint:**

```
POST /api/collections/{collection_id}/case-id-mappings/allocate
```

**Request:**

```json
{
  "localCaseId": "R1290",
  "institutionId": "002",
  "source": "sync_search_data"
}
```

**Behavior:**

1. If `localCaseId` already mapped → return existing mapping (**200**, idempotent).
2. Else allocate lowest unused `BDSA-{institutionId}-{seq:05d}` for that collection.
3. Persist atomically (Mongo transaction or equivalent) so concurrent callers never get the same ID.
4. Return:

```json
{
  "success": true,
  "collection_id": "kentucky",
  "mapping": {
    "localCaseId": "R1290",
    "bdsaCaseId": "BDSA-002-00001"
  },
  "allocated": true
}
```

For an existing mapping, `"allocated": false`.

**Consumer change after this ships:** `sync_uk_case_id_mappings.py` can call allocate per folder instead of client-side sequence scanning.

---

### P1 — Validate without writing

**New endpoint:**

```
POST /api/collections/{collection_id}/case-id-mappings/validate
```

**Request:** same body as merge (`CaseIdMappingsPayload` with one or more proposed `mappings`).

**Response:**

```json
{
  "success": true,
  "valid": false,
  "conflicts": [
    {
      "kind": "bdsa_case_id_taken",
      "localCaseId": "R1292",
      "bdsaCaseId": "BDSA-002-00002",
      "existingLocalCaseId": "R1291"
    }
  ]
}
```

Does not modify stored data. Useful for dry-run in UI and in sync scripts.

---

### P1 — Lookup by `bdsaCaseId` (**requested — high value**)

**New endpoint:**

```
GET /api/collections/{collection_id}/case-id-mappings/by-bdsa/{bdsaCaseId}
```

**Success (200):**

```json
{
  "success": true,
  "collection_id": "kentucky",
  "mapping": {
    "localCaseId": "R1290",
    "bdsaCaseId": "BDSA-002-00001"
  }
}
```

**Not found (404):**

```json
{
  "detail": "bdsaCaseId not found",
  "bdsaCaseId": "BDSA-002-99999"
}
```

**Why we need this:** pub-data sync, portal, and audit tools often have a BDSA case ID (from folder meta or slide metadata) and need the local case ID (`R1290`) without downloading the entire mapping table. This is especially important as Kentucky scales beyond the initial 14-folder pilot.

**Optional companion (same priority):**

```
GET /api/collections/{collection_id}/case-id-mappings/by-local/{localCaseId}
```

Same response shape; **404** if unmapped.

**Index requirement:** Mongo (or equivalent) unique index on `(collection_id, bdsaCaseId)` and `(collection_id, localCaseId)`.

---

### P2 — Bulk allocate

**New endpoint (optional):**

```
POST /api/collections/{collection_id}/case-id-mappings/allocate-batch
```

**Request:**

```json
{
  "institutionId": "002",
  "localCaseIds": ["R1290", "R1291", "R1292"],
  "source": "sync_search_data"
}
```

**Response:** array of `{ localCaseId, bdsaCaseId, allocated }`. All-or-nothing transaction preferred.

---

### P2 — Region label mappings (**see §8**)

Collection-level registry: `REGIONO` free text → `regionProtocolId`. Endpoints mirror case-id-mappings (`GET`, `PUT`, `merge`, `validate`, `by-label/{normalized}`). Interim consumer uses `ukRegionOLabels` on GET `/protocols` until this ships.

---

## 6. Suggested error model (shared across endpoints)

Use a consistent conflict structure so clients can programmatically handle errors:

| `kind` | Meaning |
|--------|---------|
| `local_case_reassigned` | `localCaseId` already bound to another `bdsaCaseId` |
| `duplicate_bdsa_case_id` | `bdsaCaseId` already bound to another `localCaseId` |
| `invalid_bdsa_case_id` | Format / institution mismatch |
| `institution_mismatch` | `bdsaCaseId` institution ≠ collection institution |
| `region_label_reassigned` | `normalized` label already bound to another `regionProtocolId` |
| `duplicate_region_label` | Same `regionLabel`/`normalized` registered twice in one payload |
| `unknown_region_protocol` | `regionProtocolId` not in collection `regionProtocols` |
| `stain_label_reassigned` | (stain-label-mappings) same pattern as region |

HTTP status: **409** for conflicts, **422** for malformed IDs, **404** for unknown collection.

---

## 7. Acceptance tests (for the API agent)

Run against a test collection or `kentucky` in dev.

```bash
export API=https://api.bdsa.io
export KEY=$BDSA_API_KEY
export CID=kentucky
```

**Test A — idempotent merge**

```bash
# First merge
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"institutionId":"002","mappings":[{"localCaseId":"TEST-A","bdsaCaseId":"BDSA-002-90001"}]}' \
  "$API/api/collections/$CID/case-id-mappings/merge"

# Same again → 200, unchanged
```

**Test B — reject localCaseId reassignment (after P0)**

```bash
# Should return 409
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"institutionId":"002","mappings":[{"localCaseId":"TEST-A","bdsaCaseId":"BDSA-002-90002"}]}' \
  "$API/api/collections/$CID/case-id-mappings/merge"
```

**Test C — reject duplicate bdsaCaseId (after P0)**

```bash
# Should return 409
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"institutionId":"002","mappings":[{"localCaseId":"TEST-B","bdsaCaseId":"BDSA-002-90001"}]}' \
  "$API/api/collections/$CID/case-id-mappinash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"localCaseId":"TEST-C","institutionId":"002","source":"acceptance-test"}' \
  "$API/api/collections/$CID/case-id-mappings/allocate"
# Second call same localCaseId → same bdsaCaseId, allocated=false
```

**Test E — lookup by BDSA ID (after P1 lookup ships)**

```bash
# After TEST-A merged
curl -s -H "X-API-Key: $KEY" \
  "$API/api/collections/$CID/case-id-mappings/by-bdsa/BDSA-002-90001"
# → {"success":true,"mapping":{"localCaseId":"TEST-A","bdsaCaseId":"BDSA-002-90001"}}

curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $KEY" \
  "$API/api/collections/$CID/case-id-mappings/by-bdsa/BDSA-002-99999"
# → 404

curl -s -H "X-API-Key: $KEY" \
  "$API/api/collections/$CID/case-id-mappings/by-local/TEST-A"
# → same mapping
```

Clean up test rows after (`TEST-A`, `TEST-B`, `TEST-C`) via admin or filtered delete if available.

---

## 8. Region label mappings (P2) — REGIONO → region protocol

### 8.1 Problem

UK slide CSV columns:

| Column | Meaning |
|--------|---------|
| `REGION` | Numeric survey block index (1–14) or `15` (other / sub-site) |
| `REGIONO` | Free-text brain site when `REGION=15` or when a finer label is recorded |

When `REGIONO` is present, we map that text to one of the **14 kentucky survey block region protocols** (e.g. `Entorhinal cortex` → `kentucky_region_amygdala`). This is a **collection-level crosswalk**, not per-case data.

**Coverage today (confirmed aliases):** ~21 distinct `REGIONO` strings → 12 region protocols (~3,900 slides). ~12,600 slides still unmapped: numeric `REGION` 1–14 without `REGIONO` need **block→region** (`block2region` API); many `REGION=15` labels are finer than the survey blocks and need curator review before registration.

**Related but separate:** `block2region` maps **per-case block indices** to region protocols. Region label mappings map **global free-text labels** (`REGIONO`) to protocols. Both are needed.

### 8.2 Interim workaround (works today, not ideal long-term)

Until dedicated endpoints ship, the consumer can store labels on each region protocol document:

```
PUT /api/collections/{collection_id}/protocols
```

Add optional array field on each `regionProtocols[]` entry:

```json
{
  "id": "kentucky_region_amygdala",
  "name": "Amygdala",
  "ukRegionOLabels": ["Entorhinal cortex"]
}
```

**Observed behavior (2026-06-08):**

- `PUT /protocols` **does** persist extra fields such as `ukRegionOLabels`.
- `POST /protocols/merge` **does not** update existing protocol ids (new fields on existing protocols are ignored).

**Consumer script:** `sync_uk_regiono_mappings.py` (dry-run by default; `--apply` does full protocols PUT).

**Limitations of the workaround:**

- Requires full protocols document replace to update labels.
- No lookup-by-label endpoint; clients scan all `regionProtocols`.
- No server-side 409 on label reassignment or duplicate labels across protocols.
- UK-specific field name on protocol objects; other collections need parallel ad-hoc fields.

### 8.3 Proposed resource: `region-label-mappings`

Mirror the **case-id-mappings** pattern: a first-class registry per collection.

#### Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/collections/{collection_id}/region-label-mappings` | Read all mappings |
| PUT | `/api/collections/{collection_id}/region-label-mappings` | Full replace |
| POST | `/api/collections/{collection_id}/region-label-mappings/merge` | Merge by `normalized` |
| POST | `/api/collections/{collection_id}/region-label-mappings/validate` | Dry-run validation |
| GET | `/api/collections/{collection_id}/region-label-mappings/by-label/{normalized}` | Lookup by normalized label |

OpenAPI schemas (suggested names): `RegionLabelMappingItem`, `RegionLabelMappingsPayload`, `RegionLabelMappingsResponse`.

#### Payload shape

**Request / stored document (`RegionLabelMappingsPayload`):**

```json
{
  "mappings": [
    {
      "regionLabel": "Entorhinal cortex",
      "normalized": "entorhinal cortex",
      "regionProtocolId": "kentucky_region_amygdala",
      "validated": true,
      "source": "sync_search_data"
    },
    {
      "regionLabel": "Insula",
      "normalized": "insula",
      "regionProtocolId": "kentucky_region_frontal_gyrus",
      "validated": true,
      "source": "sync_search_data"
    }
  ],
  "source": "sync_search_data",
  "version": "1.0",
  "totalMappings": 21,
  "lastUpdated": "2026-06-08T22:00:00Z"
}
```

**GET response:**

```json
{
  "success": true,
  "collection_id": "kentucky",
  "regionLabelMappings": { "... RegionLabelMappingsPayload or null ..." }
}
```

**Lookup by label (200):**

```json
{
  "success": true,
  "collection_id": "kentucky",
  "mapping": {
    "regionLabel": "Entorhinal cortex",
    "normalized": "entorhinal cortex",
    "regionProtocolId": "kentucky_region_amygdala",
    "validated": true
  }
}
```

**Not found (404):** `{ "detail": "region label not found", "normalized": "unknown site" }`

#### Normalization rule (server should apply consistently)

Same as consumer `uk_protocol_mapping._norm()`:

1. Unicode NFKD + strip combining marks  
2. Lowercase, trim  
3. Replace non-alphanumeric runs with a single space  
4. Collapse whitespace  

Example: `"Post Cingulate"` → `"post cingulate"`. Server may accept `regionLabel` only and compute `normalized`, but stored documents should include both for stable merge keys.

#### Invariants to enforce

1. **One `normalized` label → one `regionProtocolId`** (per collection).  
   Reassigning `insula` from `kentucky_region_frontal→ **409** (`region_label_reassigned`).

2. **`regionProtocolId` must exist** in the collection’s `regionProtocols` (from GET `/protocols`) → **422** (`unknown_region_protocol`).

3. **Merge is idempotent** when the same `normalized` + same `regionProtocolId` is posted again.

4. **Full PUT validates the entire payload** (same as case-id-mappings P0).

5. **`validated: false`** rows may be stored for curator review but must not be returned by lookup-by-label (or lookup returns them with a flag — pick one behavior and document it; consumer prefers **exclude unvalidated from lookup**).

#### Optional denormalized view

After PUT/merge on `region-label-mappings`, the server **may** refresh `ukRegionOLabels` on each `regionProtocols[]` entry (group validated labels by `regionProtocolId`) so GET `/protocols` stays useful for UI. Not required if all clients use the registry endpoint.

### 8.4 Initial kentucky mappings (seed data)

Consumer local registry (`registries/kentucky_regiono_protocol_mappings.json`) seeds from confirmed CSV aliases:

| `REGIONO` (display) | `regionProtocolId` |
|---------------------|-------------------|
| Entorhinal cortex | `kentucky_region_amygdala` |
| Post Cingulate | `kentucky_region_anterior_cingulate` |
| Motor Cx, Sensory Cx | `kentucky_region_central_gyri_motor_cortex` |
| Dentate, Vermis | `kentucky_region_cerebellum` |
| Frontal Pole, Insula, Olf Bulb, G. rectus | `kentucky_region_frontal_gyrus` |
| Spinal Cord | `kentucky_region_medulla` |
| Precuneus | `kentucky_region_parietal_gyrus` |
| Ponto Midbrain Infarct | `kentucky_region_pons` |
| Caudate | `kentucky_region_striatum_basal_ganglia` |
| Temporal Pole, Inferior Temporal | `kentucky_region_temporal_lobe` |
| Hypothalamus | `kentucky_region_thalamus` |
| Cuneus, Occ. pole | `kentucky_region_visual_cortex_occipital` |

Full list (~21 rows) lives in `sync_search_data/uk_protocol_mapping.py` (`REGIONO_ALIASES`) and the JSON registry.

### 8.5 Optional companion: `stain-label-mappings` (P3)

Same shape for `STAINO` free text → `stainProtocolId`:

| `STAINO` | `stainProtocolId` |
|----------|-------------------|
| PHF-1 | `kentucky_tau` |
| Nab228 | `kentucky_abeta` |

Numeric `STAIN` codes 1–5 already map 1:1 to protocols; stain-label-mappings only needed for overrides and non-standard aliases. Lower priority than region labels.

### 8.6 Acceptance tests (region label mappings)

```bash
export API=https://api.bdsa.io
export KEY=$BDSA_API_KEY
export CID=kentucky
```

**Test F — merge idempotent**

```bash
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mappings":[{"regionLabel":"TEST-SITE","normalized":"test site","regionProtocolId":"kentucky_region_amygdala","validated":true}],"source":"acceptance-test"}' \
  "$API/api/collections/$CID/region-label-mappings/merge"

# Same again → 200, unchanged
```

**Test G — reject label reassignment**

```bash
# Should return 409
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mappings":[{"regionLabel":"TEST-SITE","normalized":"test site","regionProtocolId":"kentucky_region_frontal_gyrus","validated":true}]}' \
  "$API/api/collections/$CID/region-label-mappings/merge"
```

**Test H — lookup by normalized label**

```bash
curl -s -H "X-API-Key: $KEY" \
  "$API/api/collections/$CID/region-label-mappings/by-label/test%20site"
# → mapping with kentucky_region_amygdala

curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $KEY" \
  "$API/api/collections/$CID/region-label-mappings/by-label/no-such-site"
# → 404
```

**l id**

```bash
# Should return 422
curl -X POST -H "X-API-Key: $KEY" -H "Content-Type: application/json" \
  -d '{"mappings":[{"regionLabel":"BAD","normalized":"bad","regionProtocolId":"not_a_real_protocol","validated":true}]}' \
  "$API/api/collections/$CID/region-label-mappings/merge"
```

Clean up test row `test site` after.

### 8.7 Consumer workflow (after endpoint ships)

```
1. GET /api/collections/kentucky/region-label-mappings
2. Reconcile with registries/kentucky_regiono_protocol_mappings.json
3. audit_uk_protocols.py — find new REGIONO labels needing curator review
4. Add validated rows to local registry
5. On --apply (sync_uk_regiono_mappings.py):
     - POST .../region-label-mappings/merge with new/changed rows only
     - save local registry
     - resolve_region_protocol() prefers upstream registry over local aliases
```

**Migration:** One-time import from interim `ukRegionOLabels` on GET `/protocols` into the new registry, then treat the registry as source of truth.

---

## 9. Related endpoints we will use next

Not blocking case IDs, but planned consumer work:

| Resource | Endpoint | Use |
|----------|----------|-----|
| Slides | `GET/PUT /api/collections/kentucky/slides` | Register slide-level BDSA metadata |
| Block→region | `PUT .../cases/{case_id}/block2region` | Per-case survey block index → region protocol |
| Region label mappings | `GET/PUT/merge .../region-label-mappings` | **P2 —** global `REGIONO` text → region protocol |
| Stain label mappings | `GET/PUT/merge .../stain-label-mappings` | **P3 —** optional `STAINO` text → stain protocol |
| Patient ID mappings | `GET/PUT .../patient-id-mappings` | If UK local patient ≠ case ID |
| Protocols | `GET /api/collections/kentucky/protocols` | Protocol definitions; interim `ukRegionOLabels` storage |

Stain protocol IDs on `kentucky` today include: `kentucky_he`, `kentucky_abeta`, `kentucky_tau`, `kentucky_asyn`, `kentucky_tdp43`, `ignore_stain`.

---

## 10. Consumer workflow (today, without new endpoints)

```
1. GET /api/collections/kentucky/case-id-mappings
2. Reconcile with local registry (registries/kentucky_case_id_mappings.json)
3. List Girder patient folders (R1290, …)
4. For each unmapped folder:
     - pick lowest BDSA-002-NNNNN not present upstream or locally
     - validate 1:1 constraints client-side
5. On --apply:
     - GET case-id-mappings again (fresh snapshot)
     - abort if collision
     - POST .../case-id-mappings/merge with new rows only
     - save local registry
     - optionally write meta.bdsa.bdsa_case_id on Girder folder
```

Once **P0** ships, step 5 fails safely if upstream changed.  
Once **P1 allocate** ships, steps 4–5 simplify to one POST per case.

**Region labels (interim):** use `sync_uk_regiono_mappings.py --apply` (protocols PUT + `ukRegionOLabels`) until **§8 region-label-mappings** ships; then switch merge target to the new registry.

---

## 11. Contact / repo pointers

| Item | Location |
|------|----------|
| API docs (this repo) | `docs/schema_api.md` |
| This handoff | `docs/schema_api_integration_requests.md` |
| Case ID sync script | `sync_search_data/sync_uk_case_id_mappings.py` |
| REGIONO / region protocol sync | `sync_search_data/sync_uk_regiono_mappings.py` |
| Protocol audit (CSV vs API) | `sync_search_data/audit_uk_protocols.py` |
| Slide metadata sync | `sync_search_data/sync_uk_item_metadata.py` |
| UK CSV source | `docs/uk_slide_level_metadata_to_export.csv` |
| REGIONO mapping rules (code) | `sync_search_data/uk_protocol_mapping.py` |
| Girder UK collection | `UK_CollectionId=6a272431575499fab2a820ad` (`BDSA_UK_Thumbs`) |

When implementing, update OpenAPI (`/docs`) and ping the pub-data agent so `schema_client.py` can adopt new endpoints.
