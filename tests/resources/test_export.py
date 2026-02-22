import os
import tempfile
from tests.conftest import my_vcr
from didww.enums import ExportStatus, ExportType
from didww.resources.export import Export


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

    @my_vcr.use_cassette("exports/create.yaml")
    def test_create_export(self, client):
        export = Export()
        export.export_type = ExportType.CDR_IN
        export.filters = {"did_number": "1234556789", "year": "2019", "month": "01"}
        response = client.exports().create(export)
        created = response.data
        assert created.id == "da15f006-5da4-45ca-b0df-735baeadf423"
        assert created.status == ExportStatus.PENDING

    @my_vcr.use_cassette("exports/download.yaml")
    def test_download_export_to_path(self, client):
        url = "https://sandbox-api.didww.com/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            dest = f.name
        try:
            client.download_export(url, dest)
            with open(dest, "r") as f:
                content = f.read()
            assert "Date/Time Start (UTC)" in content
            assert "972397239159652" in content
        finally:
            os.unlink(dest)

    @my_vcr.use_cassette("exports/download.yaml")
    def test_download_export_to_file_object(self, client):
        url = "https://sandbox-api.didww.com/v3/exports/02bf6df4-3af9-416c-96be-16e5b7eeb651.csv"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            dest = f.name
        try:
            with open(dest, "wb") as f:
                client.download_export(url, f)
            with open(dest, "r") as f:
                content = f.read()
            assert "Date/Time Start (UTC)" in content
        finally:
            os.unlink(dest)
