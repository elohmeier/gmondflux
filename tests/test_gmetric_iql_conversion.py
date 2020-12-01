import logging
import socket
import subprocess

from collections import OrderedDict
from gmondflux.gmondflux import recv_packet

logger = logging.getLogger(__name__)


def gmetric_iql(metric_name: str, value_type: str, value: str):
    metric_type_cache = OrderedDict()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_server:
        # set timeout to let the test fail if gmetric sends no packets.
        udp_server.settimeout(1)

        udp_server.bind(("127.0.0.1", 8679))
        subprocess.call(
            [
                "gmetric",
                "--conf=%s" % "configs/gmetric.conf",
                "--name=%s" % metric_name,
                "--value=%s" % value,
                "--type=%s" % value_type,
                "--units=bla",
            ]
        )

        metadata_packet = recv_packet(udp_server, metric_type_cache)
        assert metadata_packet.is_metadata_packet

        value_packet = recv_packet(udp_server, metric_type_cache)
        assert not value_packet.is_metadata_packet

        udp_server.close()

        iql = value_packet.iql()
        return iql


def test_string():
    assert (
        gmetric_iql("my_metric", "string", "abcxyzöäü")
        == 'gmond,host=mywebserver.domain.com my_metric="abcxyzöäü"\n'
    )


def test_float():
    assert (
        gmetric_iql("my_metric", "float", "1.234")
        == "gmond,host=mywebserver.domain.com my_metric=1.234\n"
    )


def test_int():
    assert (
        gmetric_iql("my_metric", "int32", "1234")
        == "gmond,host=mywebserver.domain.com my_metric=1234i\n"
    )
