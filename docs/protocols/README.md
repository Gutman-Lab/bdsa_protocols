# Survey-derived protocols

Extracted from `docs/ADRC_Neuropath_Survey2026-06-01_14_41_40.csv` (one submission per institution).

| File | Institution | Survey date |
|------|-------------|-------------|
| `emory-adrc-survey-protocols.json` | Emory University | Aug 17, 2022 |
| `kentucky-adrc-survey-protocols.json` | U. Kentucky | Jul 15, 2022 |
| `uc-davis-adrc-survey-protocols.json` | UC Davis | Jun 29, 2022 |
| `pittsburgh-adrc-survey-protocols.json` | Pittsburgh | Jun 9, 2022 |

## Regenerate all

```bash
python scripts/extract_adrc_survey_protocols.py
```

Single institution:

```bash
python scripts/extract_adrc_survey_protocols.py --institution pittsburgh
```

## Import into Mongo (API must be running)

Generating JSON alone does **not** update the app. You must pass **`--import`**:

```bash
python scripts/extract_adrc_survey_protocols.py --import --api http://localhost:8000
```

This creates **one collection per university** (separate Mongo `collection_id`):

| `collection_id` | Display name (in UI) |
|-----------------|----------------------|
| `emory` | Emory University |
| `kentucky` | U. Kentucky |
| `uc-davis` | UC Davis |
| `pittsburgh` | Pittsburgh |

The protocols page dropdown only lists collections that have data in Mongo. After import, refresh http://localhost:3000/protocols and choose the institution from the collection picker (not only `1` / “Emory Base” unless you imported there).

## Institution-specific notes

- **Pittsburgh** — survey reports **Nova red** chromogen (mapped to `AEC (Red)`); planning switch to DAB noted in survey text.
- **Kentucky** — amyloid vendor **NAB228** (antibody `unknown` in Pitt schema); bilateral hemisphere.
- **UC Davis** — tau **AT8**; section thickness **5–7 µm** (stored as 6.0 average).
- **Emory** — phospho α-syn (WAKO Syn #64); TDP-43 Cosmo Bio clone.
