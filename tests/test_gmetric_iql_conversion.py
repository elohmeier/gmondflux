import socket
import subprocess

from gmondflux.gmondflux import recv_packet

# to run this tests, make sure gmetric is in your PATH


def gmetric_iql(
    metric_name: str, value_type: str, value: str, convert_numeric: bool = False
):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_server:
        # set timeout to let the test fail if gmetric sends no packets.
        udp_server.settimeout(1)

        udp_server.bind(("127.0.0.1", 8679))
        subprocess.call(
            [
                "gmetric",
                "-c",
                "configs/gmetric.conf",
                "-n",
                metric_name,
                "-t",
                value_type,
                "-v",
                value,
            ]
        )

        metadata_packet = recv_packet(udp_server, convert_numeric)
        assert metadata_packet.is_metadata_packet

        value_packet = recv_packet(udp_server, convert_numeric)
        assert not value_packet.is_metadata_packet

        udp_server.close()

        iql = value_packet.iql()
        return iql


def test_string():
    assert (
        gmetric_iql("my_metric", "string", "abcxyzöäü")
        == 'gmond,host=mywebserver.domain.com my_metric="abcxyzöäü"\n'
    )


def test_string_conversion():
    assert (
        gmetric_iql("my_metric", "string", "0", convert_numeric=False)
        == 'gmond,host=mywebserver.domain.com my_metric="0"\n'
    )

    assert (
        gmetric_iql("my_metric", "string", "0", convert_numeric=True)
        == "gmond,host=mywebserver.domain.com my_metric=0\n"
    )
