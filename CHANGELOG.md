# Changelog for ndx-brainstem

## 0.2.0 (unreleased)

- `BrainstemSchemaTable` gets a required `schema_url` column: the stable URL of each BrainSTEM schema version
  (`https://www.brainstem.org/schemas/<Family>/<Type>/<version>.json`). `schema_json` may be empty when the schema
  was not embedded.
- `BrainstemTable` gets an optional `coordinates_schema` column, like `details_schema`.

## 0.1.0

- `BrainstemMetadata` (LabMetaData) with export provenance attributes.
- `BrainstemTable`: generic table of BrainSTEM records, one column per field, ragged links between tables.
- `BrainstemSchemaTable`: the BrainSTEM JSON schemas named by the tables.
