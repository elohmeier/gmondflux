import requests

# noinspection PyUnresolvedReferences
from tests.fixtures import influxdb_port


def test_connection_to_influxdb(influxdb_port):
    res = requests.get(f"http://localhost:{influxdb_port}", timeout=2)
    assert res.status_code == 404
