# -*- coding: utf-8 -*-
"""
Generate spec/ndx-brainstem.namespace.yaml and spec/ndx-brainstem.extensions.yaml.

The extension stores BrainSTEM records as generic tables: one row per record, one column per
BrainSTEM field, and links between rows as (ragged) DynamicTableRegions. Which fields a table
has follows the BrainSTEM data model, so the schema does not change when BrainSTEM adds a field
or a typed JSON schema: only the two identity columns are required.

    python src/spec/create_extension_spec.py
"""
from pathlib import Path

import ndx_anatomical_localization  # noqa: F401  (loads the namespace included below)
from pynwb.spec import NWBAttributeSpec, NWBDatasetSpec, NWBGroupSpec, NWBNamespaceBuilder, export_spec


def main():
    ns_builder = NWBNamespaceBuilder(
        name="""ndx-brainstem""",
        version="""0.1.0""",
        doc="""BrainSTEM (https://www.brainstem.org) experimental metadata in NWB: the BrainSTEM records an NWB
file was made from, with every field and the links between them.""",
        author=["BrainSTEM Team"],
        contact=["petersen.peter@gmail.com"],
    )
    ns_builder.include_namespace("core")
    # Coordinates of BrainSTEM procedures and interfaces are written with ndx-anatomical-localization, whose
    # tables link to rows of BrainstemTables; including its namespace lets validators resolve those links.
    ns_builder.include_namespace("ndx-anatomical-localization")

    brainstem_table = NWBGroupSpec(
        neurodata_type_def="BrainstemTable",
        neurodata_type_inc="DynamicTable",
        doc=(
            "BrainSTEM records of one kind (procedures, materials, interfaces, ...), one row per record. Besides "
            "the required columns, a table has one column per BrainSTEM field of its records, named as the field. "
            "Text columns hold strings as stored and other values (numbers, booleans, JSON objects such as a "
            "record's typed details) as JSON; an empty string means no value. A field that links to records in "
            "another BrainstemTable (or to the NWB epochs table) is a ragged DynamicTableRegion with the same name; "
            "links to records not in the file are listed in the 'unresolved_links' column."
        ),
        attributes=[
            NWBAttributeSpec(
                name="brainstem_models",
                doc="BrainSTEM model labels of the rows, e.g. 'modules.procedure'.",
                dtype="text",
                shape=[None],
            ),
        ],
        datasets=[
            NWBDatasetSpec(
                name="brainstem_id",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc="BrainSTEM id of the record (a UUID; user ids are integers written as text).",
            ),
            NWBDatasetSpec(
                name="brainstem_model",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc="BrainSTEM model label of the record, e.g. 'modules.procedure'.",
            ),
            NWBDatasetSpec(
                name="details_schema",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc=(
                    "BrainSTEM JSON schema of the record's typed details, as '<Family>/<Type>@<version>' (e.g. "
                    "'Procedure/VirusInjection@3.0.0'); empty when the record has no typed details. The schema "
                    "itself is in the 'schemas' table when the export provided it."
                ),
                quantity="?",
            ),
            NWBDatasetSpec(
                name="unresolved_links",
                neurodata_type_inc="VectorData",
                dtype="text",
                doc="JSON object {field: [BrainSTEM ids]} of links to records that are not in this file.",
                quantity="?",
            ),
        ],
    )

    schema_table = NWBGroupSpec(
        neurodata_type_def="BrainstemSchemaTable",
        neurodata_type_inc="DynamicTable",
        doc="The BrainSTEM JSON schemas that the 'details_schema' columns name, as JSON text.",
        datasets=[
            NWBDatasetSpec(name="schema_id", neurodata_type_inc="VectorData", dtype="text",
                           doc="'<Family>/<Type>@<version>', as in the details_schema columns."),
            NWBDatasetSpec(name="schema_json", neurodata_type_inc="VectorData", dtype="text",
                           doc="The JSON schema (draft 7) as JSON text."),
        ],
    )

    metadata = NWBGroupSpec(
        neurodata_type_def="BrainstemMetadata",
        neurodata_type_inc="LabMetaData",
        default_name="brainstem",
        doc=(
            "The BrainSTEM metadata of this file: where it was exported from, and the BrainSTEM records it was "
            "made from as BrainstemTables. Written by brainstem-nwb."
        ),
        attributes=[
            NWBAttributeSpec(name="export_format_version", dtype="text",
                             doc="Version of the BrainSTEM export the file was made from, e.g. '2.1'."),
            NWBAttributeSpec(name="export_scope", dtype="text", doc="'project' or 'session'."),
            NWBAttributeSpec(name="exported_at", dtype="text", doc="When the BrainSTEM export was made (ISO 8601)."),
            NWBAttributeSpec(name="source_sha256", dtype="text", doc="sha256 of the BrainSTEM export."),
            NWBAttributeSpec(name="project_ids", dtype="text", shape=[None],
                             doc="BrainSTEM ids of the projects the session belongs to."),
            NWBAttributeSpec(name="session_id", dtype="text", doc="BrainSTEM id of the session."),
            NWBAttributeSpec(name="subject_id", dtype="text", required=False,
                             doc="BrainSTEM id of the subject (absent for files without a subject)."),
            NWBAttributeSpec(name="unit_id", dtype="text",
                             doc="brainstem-nwb unit id: '<session id>__<subject id>'."),
            NWBAttributeSpec(name="exporter", dtype="text", doc="Software that wrote the metadata (brainstem-nwb)."),
            NWBAttributeSpec(name="exporter_version", dtype="text", doc="Version of the exporter."),
            NWBAttributeSpec(name="mapping_version", dtype="text",
                             doc="Version of the exporter's BrainSTEM-to-NWB mapping."),
            NWBAttributeSpec(name="content_sha256", dtype="text",
                             doc="Digest of the planned NWB content; the NWB identifier is derived from it."),
        ],
        groups=[
            NWBGroupSpec(neurodata_type_inc="BrainstemTable", quantity="*",
                         doc="One table per kind of BrainSTEM record (procedures, materials, interfaces, ...)."),
            NWBGroupSpec(neurodata_type_inc="BrainstemSchemaTable", name="schemas", quantity="?",
                         doc="BrainSTEM JSON schemas named by the tables."),
        ],
    )

    export_spec(ns_builder, [brainstem_table, schema_table, metadata],
                str((Path(__file__).parent.parent.parent / "spec").absolute()))


if __name__ == "__main__":
    main()
