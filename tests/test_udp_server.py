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
    assert len(q) == 1
    value_packet = q.get()
    assert value_packet.packet_type == 133  # float

    assert value_packet.metric_name == "cpu_idle"
