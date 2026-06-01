# BDSA JSON Schemas (Pitt canonical)

Split schemas from [pitt-bdsa/bdsa](https://github.com/pitt-bdsa/bdsa/tree/main/girder-plugins/girder-bdsa/girder_bdsa/schemas):

| File | Description |
|------|-------------|
| `clinical-metadata.json` | Case-level clinical / NACC fields |
| `region-metadata.json` | Region IDs and landmarks |
| `stain-metadata.json` | Stain IDs and staining parameters |
| `slide-level-metadata.json` | Per-slide `bdsa_case_id`, `block_id` |

To refresh from upstream:

```bash
for f in clinical-metadata region-metadata stain-metadata slide-level-metadata; do
  gh api "repos/pitt-bdsa/bdsa/contents/girder-plugins/girder-bdsa/girder_bdsa/schemas/${f}.json" \
    -H "Accept: application/vnd.github.raw" \
    > "frontend/public/schemas/${f}.json"
done
```
