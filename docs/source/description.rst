Overview
========

``ndx-brainstem`` stores `BrainSTEM <https://www.brainstem.org>`_ experimental metadata inside an NWB file:
the BrainSTEM records the file was made from, with every field, and the links between them.

``/general/brainstem`` (``BrainstemMetadata``, a ``LabMetaData``) holds the export provenance as attributes and
one ``BrainstemTable`` per kind of record (procedures, materials, interfaces, acquisitions, ...). A table has one
row per record and one column per BrainSTEM field; links between records are ragged ``DynamicTableRegion``
columns that point only to earlier tables, so the tables form no cycle. ``BrainstemSchemaTable`` lists every
BrainSTEM JSON schema the ``details_schema`` and ``coordinates_schema`` columns name, with its stable URL
(``schema_url``) and, when embedded, the schema itself (``schema_json``).

The namespace includes ``ndx-anatomical-localization``, whose coordinate tables can localize rows of
``BrainstemTable``\ s (procedures and interfaces).

Files are written by `brainstem-nwb <https://github.com/brainstem-org/brainstem-nwb>`_.
