from gmondflux.gmond_client import read_cluster_name

# noinspection PyUnresolvedReferences
from .fixtures import gmond_port


def test_gmond_read_xml(gmond_port):
    cn = read_cluster_name("localhost", gmond_port)
    assert cn == "pytestcluster"
