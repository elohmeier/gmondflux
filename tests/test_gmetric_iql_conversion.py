import subprocess

from gmondflux.gmondflux import udp_server, recv_packet

# to run this tests, make sure gmetric is in your PATH


def test_string():
    # set timeout to let the test fail if gmetric sends no packets.
    udp_server.settimeout(1)

    udp_server.bind(("127.0.0.1", 8679))
    subprocess.call(
        [
            "gmetric",
            "-c",
            "configs/gmetric.conf",
            "-n",
            "my_metric",
            "-t",
            "string",
            "-v",
            "abcxyzöäü",
        ]
    )

    metadata_packet = recv_packet()
    assert metadata_packet.is_metadata_packet

    value_packet = recv_packet()
    assert not value_packet.is_metadata_packet

    udp_server.close()

    iql = value_packet.iql()
    assert iql == 'gmond,host=mywebserver.domain.com my_metric="abcxyzöäü"\n'
