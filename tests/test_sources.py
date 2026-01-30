import pytest
from tilegrab.sources import OSM, GoogleSat, ESRIWorldImagery, Nearmap


def test_osm_get_url():
    osm = OSM()
    url = osm.get_url(10, 1, 2)
    assert url != "" and url


def test_google_sat_get_url():
    gs = GoogleSat()
    url = gs.get_url(10, 1, 2)
    assert url != "" and url


def test_esri_get_url():
    esri = ESRIWorldImagery()
    url = esri.get_url(10, 1, 2)
    assert url != "" and url


def test_nearmap_get_url():
    nm = Nearmap(api_key="test_key")
    url = nm.get_url(10, 1, 2)
    assert url != "" and url


def test_nearmap_no_key():
    nm = Nearmap()
    with pytest.raises(AssertionError):
        nm.get_url(10, 1, 2)


def test_headers_default():
    osm = OSM()
    headers = osm.headers()
    assert "user-agent" in headers


def test_headers_custom():
    custom_headers = {"custom": "header"}
    osm = OSM(headers=custom_headers)
    headers = osm.headers()
    assert headers == custom_headers