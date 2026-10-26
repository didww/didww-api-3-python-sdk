import os
import tempfile
from tests.conftest import my_vcr
from didww.enums import ExportStatus, ExportTrunkType, ExportType
from didww.resources.export import Export


class TestExportStatusHelpers:
    def test_is_pending(self):
        export = Export()
        export.status = ExportStatus.PENDING
        assert export.is_pending is True
        assert export.is_processing is False
        assert export.is_completed is False

    def test_is_processing(self):
        export = Export()
        export.status = ExportStatus.PROCESSING
        assert export.is_processing is True
        assert export.is_pending is False
        assert export.is_completed is False

    def test_is_completed(self):
        export = Export()
        export.status = ExportStatus.COMPLETED
        assert export.is_completed is True
        assert export.is_pending is False
        assert export.is_processing is False


class TestExport:
    @my_vcr.use_cassette("exports/list.yaml")
    def test_list_exports(self, client):
        response = client.exports().list()
        assert len(response.data) > 0

    @my_vcr.use_cassette("exports/show.yaml")
    def test_find_export(self, client):
        response = client.exports().find("da15f006-5da4-45ca-b0df-735baeadf423")
        export = response.data
        assert export.id == "da15f006-5da4-45ca-b0df-735baeadf423"
        assert export.status == ExportStatus.COMPLETED
        assert export.export_type == ExportType.CDR_IN
        assert export.external_reference_id == "monthly-cdr-2026-04"

    @my_vcr.use_cassette("exports/create.yaml")
    def test_create_export(self, client):
        export = Export()
        export.export_type = ExportType.CDR_IN
        export.filters = {"did_number": "1234556789", "from": "2026-04-01 00:00:00", "to": "2026-04-15 23:59:59"}
        response = client.exports().create(export)
        created = response.data
        assert created.id == "da15f006-5da4-45ca-b0df-735baeadf423"
        assert created.status == ExportStatus.PENDING

    @my_vcr.use_cassette("exports/create_sms_in.yaml")
    def test_create_sms_in_export(self, client):
        export = Export()
        export.export_type = ExportType.SMS_IN
        export.filters = {
            "from": "2026-10-01 00:00:00",
            "to": "2026-10-15 00:00:00",
            "trunk_type": [ExportTrunkType.SMPP_SMSC, ExportTrunkType.HTTP_IN],
            "destination_address_eq": "12125550100",
        }
        created = client.exports().create(export).data
        assert created.id == "5a2d3e4f-6b7c-4d8e-9f0a-1b2c3d4e5f60"
        assert created.export_type == ExportType.SMS_IN
        assert created.filters["trunk_type"] == ["SMPP SMSC", "HTTP IN"]

    @my_vcr.use_cassette("exports/create_sms_out.yaml")
    def test_create_sms_out_export(self, client):
        export = Export()
        export.export_type = ExportType.SMS_OUT
        export.filters = {
            "from": "2026-10-01 00:00:00",
            "to": "2026-10-15 00:00:00",
            "sms_trunk.id": ["b2c3d4e5-0000-4000-8000-000000000001", "b2c3d4e5-0000-4000-8000-000000000003"],
            "service_type": "a2p",
            "sender_id_verification.id": "c3d4e5f6-0000-4000-8000-000000000002",
        }
        created = client.exports().create(export).data
        assert created.id == "4f1c2d3e-5a6b-4c7d-8e9f-0a1b2c3d4e5f"
        assert created.export_type == ExportType.SMS_OUT
        assert created.filters["service_type"] == "a2p"

    def test_filters_assignment_is_dirty(self):
        export = Export.build("da15f006-5da4-45ca-b0df-735baeadf423")
        export.filters = {"from": "2026-10-01 00:00:00"}
        assert export.to_jsonapi(include_id=True, dirty_only=True)["attributes"] == {
            "filters": {"from": "2026-10-01 00:00:00"},
        }

    def test_patch_external_reference_id_request_body(self):
        """PATCH must send exactly the id, type, and only the dirty attribute."""
        export = Export.build("da15f006-5da4-45ca-b0df-735baeadf423")
        export.external_reference_id = "renamed-ref-99"
        doc = export.to_jsonapi(include_id=True, dirty_only=True)
        assert doc == {
            "id": "da15f006-5da4-45ca-b0df-735baeadf423",
            "type": "exports",
            "attributes": {"external_reference_id": "renamed-ref-99"},
        }

    @my_vcr.use_cassette("exports/update.yaml")
    def test_update_export_external_reference_id(self, client):
        export = Export()
        export.id = "da15f006-5da4-45ca-b0df-735baeadf423"
        export.external_reference_id = "renamed-ref-99"
        response = client.exports().update(export)
        updated = response.data
        assert updated.id == "da15f006-5da4-45ca-b0df-735baeadf423"
        assert updated.external_reference_id == "renamed-ref-99"

    @my_vcr.use_cassette("exports/download.yaml")
    def test_download_export(self, client):
        url = "https://sandbox-api.didww.com/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv.gz"
        with tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False) as f:
            dest = f.name
        try:
            client.download_export(url, dest)
            with open(dest, "rb") as f:
                magic = f.read(2)
            # Verify gzip magic bytes
            assert magic == b"\x1f\x8b"
        finally:
            os.unlink(dest)

    @my_vcr.use_cassette("exports/download_decompress.yaml")
    def test_download_and_decompress_export(self, client):
        url = "https://sandbox-api.didww.com/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv.gz"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            dest = f.name
        try:
            client.download_and_decompress_export(url, dest)
            with open(dest, "r") as f:
                content = f.read()
            assert "Date/Time Start (UTC)" in content
            assert "972397239159652" in content
        finally:
            os.unlink(dest)
