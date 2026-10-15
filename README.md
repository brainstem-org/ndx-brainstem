# ndx-brainstem

An [NWB](https://www.nwb.org) extension that stores [BrainSTEM](https://www.brainstem.org) experimental metadata inside an NWB file: the BrainSTEM records the file was made from, with every field, and the links between them.

Files are written by [brainstem-nwb](https://github.com/brainstem-org/brainstem-nwb) (`brainstem-nwb export --extension brainstem`). Core NWB fields (Subject, Devices, electrode groups, epochs and the text fields) describe the experiment for every NWB reader. This extension adds the structured detail behind them, so nothing BrainSTEM records is lost.

**Status:** private, pre-release (0.1.0). The schema may change before 1.0.

## What a file contains

`/general/brainstem` (`BrainstemMetadata`, a `LabMetaData`) holds:

- **Provenance attributes:** export format version and scope, export time and checksum, the BrainSTEM project, session, subject and unit ids, and the exporter and mapping versions.
- **One `BrainstemTable` per kind of record:** `procedures`, `procedure_episodes`, `materials`, `interfaces`, `acquisitions`, `manipulations`, `behaviors`, `specimen_sets`, `specimens`, `logs`, `log_entries`, `regions`, `resources` (catalog entries, equipment, setups, assays, protocols), `people`, and others. Each row is one BrainSTEM record.
- **`schemas`** (`BrainstemSchemaTable`): the BrainSTEM JSON schemas that the tables name, when the export provides them.

### `BrainstemTable` columns

| Column | Type | Contents |
|---|---|---|
| `brainstem_id`, `brainstem_model` | required text | The record's BrainSTEM id and model label (e.g. `modules.procedure`) |
| one per BrainSTEM field | text | Strings as stored. Other values (numbers, booleans, JSON objects such as `type_json`) are JSON text. An empty string means no value |
| one per link field | ragged `DynamicTableRegion` | Rows of another `BrainstemTable`, or of `/intervals/epochs` |
| `details_schema` | text | `<Family>/<Type>@<version>` of the record's typed details, e.g. `Procedure/VirusInjection@3.0.0` |
| `unresolved_links` | text | JSON `{field: [ids]}` of links to records not in the file |

The table attribute `brainstem_models` lists the model labels of the table's rows.

## Reading

```python
from pynwb import NWBHDF5IO

with NWBHDF5IO("sub-X_ses-Y.nwb", "r") as io:
    nwbfile = io.read()
    brainstem = nwbfile.lab_meta_data["brainstem"]
    procedures = brainstem.brainstem_tables["procedures"].to_dataframe()
```

NWB stores the extension's schema in every file, so pynwb (and MatNWB) can read these files without installing this package.

## Installation (development)

```bash
pip install -e ".[dev]"   # or: pip install -e . && pip install pytest
python src/spec/create_extension_spec.py   # regenerate spec/*.yaml after changing the spec
pytest
```

This extension was created with [ndx-template](https://github.com/nwb-extensions/ndx-template).
