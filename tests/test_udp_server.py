from gevent import sleep
from subprocess import Popen

from gmondflux.udp_server import GmondReceiver


def test_receive_gmetric_message():
    q = []
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
    assert q[0]["packet_type"] == 128  # metadata
    assert q[1]["packet_type"] == 133  # float
