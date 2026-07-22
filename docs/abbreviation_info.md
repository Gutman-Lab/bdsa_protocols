# Kentucky protocol abbreviations (for Schema)

Copy these onto api.bdsa.io `regionProtocols` / `stainProtocols` so filename tokens stay consistent with DSA catalogs and `networkFilename`.

Source today: local `src/bdsa_schema/uk/protocol_catalog_map.py` (not yet on Schema).

## Fields to add (top-level on each protocol)

### Regions

| Field | Required | Example | Role |
|-------|----------|---------|------|
| `abbreviation` | **yes** | `HIPP` | Filename / `networkFilename` token |
| `schemaRegionKey` | **yes** | `Hippocampus` | DSA catalog / BDSA JSON-schema property key |
| `displayName` | recommended | `Posterior hippocampus` | Short UI label |

Keep existing `id`, `name`, `regionType`, landmarks, etc.

Constraints to enforce on the Schema page:

- `abbreviation` unique within the collection
- `schemaRegionKey` unique within the collection
- Preview: `{caseNetworkId}-{abbreviation}-{stainKey}-{mag}` e.g. `BDSA02-002-HIPP-HE-20x`

### Stains (optional parity)

| Field | Required | Example | Role |
|-------|----------|---------|------|
| `schemaStainKey` | recommended | `HE` | DSA catalog / schema property key; also used in filenames |
| `displayName` | recommended | `H&E` | UI label |

Existing `stainType` often already matches the filename token (`HE`, `Tau`, `aSyn`, …).

---

## Region protocols

| protocolId | abbreviation | schemaRegionKey | displayName |
|------------|--------------|-----------------|-------------|
| `kentucky_region_posterior_hippocampus` | `HIPP` | `Hippocampus` | Posterior hippocampus |
| `kentucky_region_anterior_cingulate` | `ACg` | `Ant_Cingulate` | Anterior cingulate |
| `kentucky_region_amygdala` | `AMYG` | `Amygdala` | Amygdala |
| `kentucky_region_midbrain` | `MB` | `Midbrain` | Midbrain |
| `kentucky_region_pons` | `PONS` | `Pons` | Pons |
| `kentucky_region_medulla` | `MED` | `Medulla` | Medulla |
| `kentucky_region_frontal_gyrus` | `FRCTX` | `Frontal` | Frontal gyrus |
| `kentucky_region_temporal_lobe` | `TEMP` | `Temporal` | Temporal lobe |
| `kentucky_region_parietal_gyrus` | `PAR` | `Parietal` | Parietal gyrus |
| `kentucky_region_visual_cortex_occipital` | `OCC` | `Occipital` | Visual cortex (occipital) |
| `kentucky_region_striatum_basal_ganglia` | `BG` | `Basal_Ganglia` | Striatum (basal ganglia) |
| `kentucky_region_thalamus` | `THAL` | `Thalamus` | Thalamus |
| `kentucky_region_cerebellum` | `CB` | `Cerebellum` | Cerebellum |
| `kentucky_region_central_gyri_motor_cortex` | `MC` | `Motor_cortex` | Central gyri (motor cortex) |

## Stain protocols

| protocolId | schemaStainKey | displayName |
|------------|----------------|-------------|
| `kentucky_he` | `HE` | H&E |
| `kentucky_tau` | `Tau` | Tau |
| `kentucky_asyn` | `aSyn` | aSyn |
| `kentucky_abeta` | `aBeta` | aBeta |
| `kentucky_tdp43` | `TDP-43` | TDP-43 |

---

## JSON (paste-friendly)

```json
{
  "collection_id": "kentucky",
  "regions": [
    {
      "protocolId": "kentucky_region_posterior_hippocampus",
      "abbreviation": "HIPP",
      "schemaRegionKey": "Hippocampus",
      "displayName": "Posterior hippocampus"
    },
    {
      "protocolId": "kentucky_region_anterior_cingulate",
      "abbreviation": "ACg",
      "schemaRegionKey": "Ant_Cingulate",
      "displayName": "Anterior cingulate"
    },
    {
      "protocolId": "kentucky_region_amygdala",
      "abbreviation": "AMYG",
      "schemaRegionKey": "Amygdala",
      "displayName": "Amygdala"
    },
    {
      "protocolId": "kentucky_region_midbrain",
      "abbreviation": "MB",
      "schemaRegionKey": "Midbrain",
      "displayName": "Midbrain"
    },
    {
      "protocolId": "kentucky_region_pons",
      "abbreviation": "PONS",
      "schemaRegionKey": "Pons",
      "displayName": "Pons"
    },
    {
      "protocolId": "kentucky_region_medulla",
      "abbreviation": "MED",
      "schemaRegionKey": "Medulla",
      "displayName": "Medulla"
    },
    {
      "protocolId": "kentucky_region_frontal_gyrus",
      "abbreviation": "FRCTX",
      "schemaRegionKey": "Frontal",
      "displayName": "Frontal gyrus"
    },
    {
      "protocolId": "kentucky_region_temporal_lobe",
      "abbreviation": "TEMP",
      "schemaRegionKey": "Temporal",
      "displayName": "Temporal lobe"
    },
    {
      "protocolId": "kentucky_region_parietal_gyrus",
      "abbreviation": "PAR",
      "schemaRegionKey": "Parietal",
      "displayName": "Parietal gyrus"
    },
    {
      "protocolId": "kentucky_region_visual_cortex_occipital",
      "abbreviation": "OCC",
      "schemaRegionKey": "Occipital",
      "displayName": "Visual cortex (occipital)"
    },
    {
      "protocolId": "kentucky_region_striatum_basal_ganglia",
      "abbreviation": "BG",
      "schemaRegionKey": "Basal_Ganglia",
      "displayName": "Striatum (basal ganglia)"
    },
    {
      "protocolId": "kentucky_region_thalamus",
      "abbreviation": "THAL",
      "schemaRegionKey": "Thalamus",
      "displayName": "Thalamus"
    },
    {
      "protocolId": "kentucky_region_cerebellum",
      "abbreviation": "CB",
      "schemaRegionKey": "Cerebellum",
      "displayName": "Cerebellum"
    },
    {
      "protocolId": "kentucky_region_central_gyri_motor_cortex",
      "abbreviation": "MC",
      "schemaRegionKey": "Motor_cortex",
      "displayName": "Central gyri (motor cortex)"
    }
  ],
  "stains": [
    {
      "protocolId": "kentucky_he",
      "schemaStainKey": "HE",
      "displayName": "H&E"
    },
    {
      "protocolId": "kentucky_tau",
      "schemaStainKey": "Tau",
      "displayName": "Tau"
    },
    {
      "protocolId": "kentucky_asyn",
      "schemaStainKey": "aSyn",
      "displayName": "aSyn"
    },
    {
      "protocolId": "kentucky_abeta",
      "schemaStainKey": "aBeta",
      "displayName": "aBeta"
    },
    {
      "protocolId": "kentucky_tdp43",
      "schemaStainKey": "TDP-43",
      "displayName": "TDP-43"
    }
  ]
}
```

## After Schema update

1. Confirm `GET /api/collections/kentucky/protocols` returns the new fields on each protocol.
2. Point `sync_uk_dsa_protocols` / catalog seed at Schema `abbreviation` + `schemaRegionKey` instead of the hardcoded map.
3. Re-seed uk-dev catalogs and spot-check a few `networkFilename`s.

### Seed script

```bash
docker compose run --rm \
  -v "$(pwd)/scripts:/scripts:ro" \
  -e BDSA_API_KEY \
  backend python /scripts/seed_kentucky_abbreviations.py \
  --api http://backend:8000
```

The Protocols UI warns when region or stain abbreviations collide within a collection (save is still allowed).
