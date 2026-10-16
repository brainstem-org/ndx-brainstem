"""Write BrainSTEM tables to an NWB file, read them back, validate, and read them without this package."""

import datetime as dt
import json
import subprocess
import sys
import warnings

import pytest
from pynwb import NWBHDF5IO, NWBFile, validate

from ndx_brainstem import BrainstemMetadata, BrainstemSchemaTable, BrainstemTable


def _nwbfile():
    nwbfile = NWBFile(
        session_description="test",
        identifier="ndx-brainstem-test",
        session_start_time=dt.datetime(2024, 4, 1, 10, tzinfo=dt.timezone.utc),
    )
    nwbfile.add_epoch(0.0, 1800.0)
    nwbfile.add_epoch(1800.0, 5400.0)
    return nwbfile


def _metadata(nwbfile):
    regions = BrainstemTable(name="regions", description="brain regions", brainstem_models=["taxonomies.anatomicalregion"])
    regions.add_column("acronym", "region acronym")
    regions.add_row(brainstem_id="r1", brainstem_model="taxonomies.anatomicalregion", acronym="CA1")

    procedures = BrainstemTable(name="procedures", description="procedures", brainstem_models=["modules.procedure"])
    procedures.add_column("type", "procedure type")
    procedures.add_column("type_json", "typed details (JSON)")
    procedures.add_column("details_schema", "BrainSTEM schema of type_json")
    procedures.add_column("target_regions", "target regions", table=regions, index=True)
    procedures.add_column("unresolved_links", "links to records not in the file (JSON)")
    procedures.add_row(brainstem_id="p1", brainstem_model="modules.procedure", type="VirusInjection",
                       type_json=json.dumps({"volume": {"value": 300, "unit": "nL"}}),
                       details_schema="Procedure/VirusInjection@3.0.0", target_regions=[0], unresolved_links="")
    procedures.add_row(brainstem_id="p2", brainstem_model="modules.procedure", type="Craniotomy", type_json="",
                       details_schema="", target_regions=[],
                       unresolved_links=json.dumps({"target_regions": ["r-missing"]}))

    acquisitions = BrainstemTable(name="acquisitions", description="data acquisitions",
                                  brainstem_models=["modules.dataacquisition"])
    acquisitions.add_column("procedures", "procedures", table=procedures, index=True)
    acquisitions.add_column("epochs", "epochs the acquisition was recorded in", table=nwbfile.epochs, index=True)
    acquisitions.add_row(brainstem_id="a1", brainstem_model="modules.dataacquisition", procedures=[0], epochs=[0, 1])

    schemas = BrainstemSchemaTable(name="schemas", description="schemas")
    schemas.add_row(schema_id="Procedure/VirusInjection@3.0.0",
                    schema_url="https://www.brainstem.org/schemas/Procedure/VirusInjection/3.0.0.json",
                    schema_json=json.dumps({"type": "object"}))

    return BrainstemMetadata(
        export_format_version="2.1", export_scope="session", exported_at="2025-01-15T12:00:00+00:00",
        source_sha256="0" * 64, project_ids=["proj-1", "proj-2"], session_id="s1", subject_id="sub1",
        unit_id="s1__sub1", exporter="brainstem-nwb", exporter_version="0.1.0", mapping_version="1.2.0",
        content_sha256="1" * 64, brainstem_tables=[regions, procedures, acquisitions], schemas=schemas,
    )


@pytest.fixture
def written(tmp_path):
    nwbfile = _nwbfile()
    nwbfile.add_lab_meta_data(_metadata(nwbfile))
    path = tmp_path / "brainstem.nwb"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with NWBHDF5IO(str(path), "w") as io:
            io.write(nwbfile)
    return path


def test_round_trip(written):
    with NWBHDF5IO(str(written), "r") as io:
        nwbfile = io.read()
        metadata = nwbfile.lab_meta_data["brainstem"]
        assert isinstance(metadata, BrainstemMetadata)
        assert (metadata.session_id, metadata.subject_id, list(metadata.project_ids)) == (
            "s1", "sub1", ["proj-1", "proj-2"])
        assert sorted(metadata.brainstem_tables) == ["acquisitions", "procedures", "regions"]
        procedures = metadata.brainstem_tables["procedures"]
        assert list(procedures["brainstem_id"][:]) == ["p1", "p2"]
        assert list(procedures.brainstem_models) == ["modules.procedure"]
        assert json.loads(procedures["type_json"][0]) == {"volume": {"value": 300, "unit": "nL"}}
        assert procedures["target_regions"][0]["acronym"].tolist() == ["CA1"]
        assert len(procedures["target_regions"][1]) == 0
        assert json.loads(procedures["unresolved_links"][1]) == {"target_regions": ["r-missing"]}
        acquisitions = metadata.brainstem_tables["acquisitions"]
        assert acquisitions["procedures"][0]["brainstem_id"].tolist() == ["p1"]
        assert acquisitions["epochs"][0]["start_time"].tolist() == [0.0, 1800.0]
        assert metadata.schemas["schema_id"][0] == "Procedure/VirusInjection@3.0.0"
        assert metadata.schemas["schema_url"][0].endswith("/schemas/Procedure/VirusInjection/3.0.0.json")


def test_schema_validation(written):
    assert list(validate(path=str(written))) == []


def test_readable_without_this_package(written):
    """The extension's schema is cached in the file, so any pynwb can read it."""
    code = (
        "import sys, warnings; warnings.simplefilter('ignore'); sys.modules['ndx_brainstem'] = None\n"
        "from pynwb import NWBHDF5IO\n"
        f"with NWBHDF5IO({str(written)!r}, 'r') as io:\n"
        "    metadata = io.read().lab_meta_data['brainstem']\n"
        "    print(type(metadata).__name__, sorted(metadata.brainstem_tables))\n"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "BrainstemMetadata ['acquisitions', 'procedures', 'regions']"


def test_identity_columns_are_required():
    table = BrainstemTable(name="t", description="t", brainstem_models=["modules.procedure"])
    with pytest.raises(ValueError):
        table.add_row(brainstem_model="modules.procedure")


def test_localization_of_brainstem_rows_validates(tmp_path):
    """ndx-anatomical-localization tables can localize rows of BrainstemTables (the namespace is included)."""
    from ndx_anatomical_localization import AnatomicalCoordinatesTable, Localization, Space

    nwbfile = _nwbfile()
    metadata = _metadata(nwbfile)
    nwbfile.add_lab_meta_data(metadata)
    procedures = metadata.brainstem_tables["procedures"]
    space = Space(name="Stereotaxic_BregmaAbsolute", space_name="Stereotaxic_BregmaAbsolute", origin="bregma",
                  units="mm", orientation="RAI")
    table = AnatomicalCoordinatesTable(name="procedures", description="target coordinates", method="recorded",
                                       space=space, target=procedures)
    table.add_row(x=1.5, y=-2.0, z=1.2, localized_entity=0)
    nwbfile.add_lab_meta_data(Localization(anatomical_coordinates_tables=[table], spaces=[space]))
    path = tmp_path / "localized.nwb"
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with NWBHDF5IO(str(path), "w") as io:
            io.write(nwbfile)
    assert list(validate(path=str(path))) == []
    with NWBHDF5IO(str(path), "r") as io:
        localized = io.read().lab_meta_data["localization"].anatomical_coordinates_tables["procedures"]
        assert localized["localized_entity"][0]["brainstem_id"].tolist() == ["p1"]
