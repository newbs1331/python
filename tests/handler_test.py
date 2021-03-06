from ipaddress import IPv4Address
import json
import os

from ipinfo.cache.default import DefaultCache
from ipinfo.details import Details
from ipinfo.handler import Handler
import pytest


def test_init():
    token = "mytesttoken"
    handler = Handler(token)
    assert handler.access_token == token
    assert isinstance(handler.cache, DefaultCache)
    assert "US" in handler.countries


def test_headers():
    token = "mytesttoken"
    handler = Handler(token)
    headers = handler._get_headers()

    assert "user-agent" in headers
    assert "accept" in headers
    assert "authorization" in headers


@pytest.mark.parametrize("n", range(5))
def test_get_details(n):
    token = os.environ.get("IPINFO_TOKEN", "")
    handler = Handler(token)
    details = handler.getDetails("8.8.8.8")
    assert isinstance(details, Details)
    assert details.ip == "8.8.8.8"
    assert details.hostname == "dns.google"
    assert details.city == "Mountain View"
    assert details.region == "California"
    assert details.country == "US"
    assert details.country_name == "United States"
    assert details.loc == "37.4056,-122.0775"
    assert details.latitude == "37.4056"
    assert details.longitude == "-122.0775"
    assert details.postal == "94043"
    assert details.timezone == "America/Los_Angeles"
    if token:
        asn = details.asn
        assert asn["asn"] == "AS15169"
        assert asn["name"] == "Google LLC"
        assert asn["domain"] == "google.com"
        assert asn["route"] == "8.8.8.0/24"
        assert asn["type"] == "business"

        company = details.company
        assert company["name"] == "Google LLC"
        assert company["domain"] == "google.com"
        assert company["type"] == "business"

        privacy = details.privacy
        assert privacy["vpn"] == False
        assert privacy["proxy"] == False
        assert privacy["tor"] == False
        assert privacy["hosting"] == False

        abuse = details.abuse
        assert (
            abuse["address"]
            == "US, CA, Mountain View, 1600 Amphitheatre Parkway, 94043"
        )
        assert abuse["country"] == "US"
        assert abuse["email"] == "network-abuse@google.com"
        assert abuse["name"] == "Abuse"
        assert abuse["network"] == "8.8.8.0/24"
        assert abuse["phone"] == "+1-650-253-0000"

        domains = details.domains
        assert domains["ip"] == "8.8.8.8"
        assert domains["total"] == 12988
        assert len(domains["domains"]) == 5


@pytest.mark.parametrize("n", range(5))
def test_get_batch_details(n):
    token = os.environ.get("IPINFO_TOKEN", "")
    if not token:
        pytest.skip("token required for batch tests")
    handler = Handler(token)
    ips = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]
    details = handler.getBatchDetails(ips)

    for ip in ips:
        assert ip in details
        d = details[ip]
        assert d["ip"] == ip
        assert d["country"] == "US"
        assert d["country_name"] == "United States"
        if token:
            assert "asn" in d
            assert "company" in d
            assert "privacy" in d
            assert "abuse" in d
            assert "domains" in d


def test_builtin_ip_types():
    handler = Handler()
    fake_details = {"country": "US", "ip": "127.0.0.1", "loc": "12.34,56.78"}

    handler._requestDetails = lambda x: fake_details

    details = handler.getDetails(IPv4Address(fake_details["ip"]))
    assert isinstance(details, Details)
    assert details.country == fake_details["country"]
    assert details.country_name == "United States"
    assert details.ip == fake_details["ip"]
    assert details.loc == fake_details["loc"]
    assert details.longitude == "56.78"
    assert details.latitude == "12.34"


def test_json_serialization():
    handler = Handler()
    fake_details = {
        "asn": {
            "asn": "AS20001",
            "domain": "twcable.com",
            "name": "Time Warner Cable Internet LLC",
            "route": "104.172.0.0/14",
            "type": "isp",
        },
        "city": "Los Angeles",
        "company": {
            "domain": "twcable.com",
            "name": "Time Warner Cable Internet LLC",
            "type": "isp",
        },
        "country": "US",
        "country_name": "United States",
        "hostname": "cpe-104-175-221-247.socal.res.rr.com",
        "ip": "104.175.221.247",
        "loc": "34.0293,-118.3570",
        "latitude": "34.0293",
        "longitude": "-118.3570",
        "phone": "323",
        "postal": "90016",
        "region": "California",
    }

    handler._requestDetails = lambda x: fake_details

    details = handler.getDetails(fake_details["ip"])
    assert isinstance(details, Details)
    assert json.dumps(details.all)
