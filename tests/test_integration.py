import time

import pytest
import requests
import socket
import subprocess

from gmond_client import read_cluster_name


def wait_for_port(port, host="localhost", timeout=5.0):
    """Wait until a port starts accepting TCP connections.
    Args:
        port (int): Port number.
        host (str): Host address on which the port should exist.
        timeout (float): In seconds. How long to wait before raising errors.
    Raises:
        TimeoutError: The port isn't accepting connection after time specified in `timeout`.
    """
    start_time = time.perf_counter()
    while True:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                break
        except OSError as ex:
            time.sleep(0.01)
            if time.perf_counter() - start_time >= timeout:
                raise TimeoutError(
                    "Waited too long for the port {} on host {} to start accepting "
                    "connections.".format(port, host)
                ) from ex


@pytest.fixture(scope="module")
def influxdb():
    p = subprocess.Popen(["influxd", "run", "-config", "influxd.conf"])
    port = 18086
    wait_for_port(port)  # wait for InfluxDB to initialize
    yield ("localhost", port)
    p.terminate()


@pytest.fixture(scope="module")
def gmond():
    p = subprocess.Popen(["gmond", "-c", "gmond.conf"])
    xml_port = 8649
    wait_for_port(xml_port)  # wait for gmond XML port to initialize
    yield xml_port
    p.terminate()


def test_connection_to_influxdb(influxdb):
    print(influxdb)
    res = requests.get(f"http://{influxdb[0]}:{influxdb[1]}", timeout=2)
    assert res.status_code == 404


def test_gmond_read_xml(gmond):
    cn = read_cluster_name("localhost", gmond)
    assert cn == "pytestcluster"
