from didww.query_params import QueryParams


def test_filter():
    params = QueryParams().filter("country.iso", "US")
    assert params.to_dict() == {"filter[country.iso]": "US"}


def test_sort():
    params = QueryParams().sort("-created_at", "name")
    assert params.to_dict() == {"sort": "-created_at,name"}


def test_include():
    params = QueryParams().include("country", "region")
    assert params.to_dict() == {"include": "country,region"}


def test_page():
    params = QueryParams().page(number=2, size=25)
    assert params.to_dict() == {"page[number]": 2, "page[size]": 25}


def test_combined():
    params = (
        QueryParams()
        .filter("country.iso", "US")
        .sort("-created_at")
        .include("country")
        .page(number=1, size=10)
    )
    d = params.to_dict()
    assert d["filter[country.iso]"] == "US"
    assert d["sort"] == "-created_at"
    assert d["include"] == "country"
    assert d["page[number]"] == 1
    assert d["page[size]"] == 10


def test_empty():
    params = QueryParams()
    assert params.to_dict() == {}
