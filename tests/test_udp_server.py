from gevent import sleep
from subprocess import Popen

from gmondflux.udp_server import GmondReceiver, PacketQueue


def test_receive_gmetric_message():
    q = PacketQueue()
    r = GmondReceiver(":8649", queue=q)
    r.start()
    Popen(
        [
            "gmetric",
            "-c",
            "gmond.conf",
            "-t",
            "float",
            "-u",
            "%",
            "-n",
            "cpu_idle",
            "-v0",
        ]
    ).wait(2)
    sleep(0.1)  # wait a bit for the msg transfer
    r.stop()
    assert len(q) == 2
    metadata_packet = q.get()
    value_packet = q.get()
    assert metadata_packet.packet_type == 128  # metadata
    assert value_packet.packet_type == 133  # float

    assert metadata_packet.metric_name == "cpu_idle"
    assert value_packet.metric_name == "cpu_idle"
