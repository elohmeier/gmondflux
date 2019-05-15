import logging
from gevent import Greenlet
from influxdb import InfluxDBClient

from gmondflux import gmond_client
from gmondflux.udp_server import PacketQueue

log = logging.getLogger(__name__)


class MessageProcessor(Greenlet):
    def __init__(
        self,
        q: PacketQueue,
        influx_client: InfluxDBClient,
        gmond_xml_port: int,
        diag: bool,
    ):
        super().__init__()
        self.diag = diag
        self._influx_client = influx_client
        self._gmond_xml_port = gmond_xml_port
        self._q = q
        self._cluster_map = {}

    def _lookup_cluster_name(self, sender_host):

        if sender_host not in self._cluster_map:
            self._cluster_map[sender_host] = gmond_client.read_cluster_name(
                sender_host, self._gmond_xml_port
            )

        return self._cluster_map[sender_host]

    def _run(self):
        while True:
            packet = self._q.get()
            log.debug(
                "processing metric %s (%s), received from %s",
                packet.metric_name,
                packet.packet_type,
                packet.sender_host,
            )

            if packet.is_metadata():  # ignore metadata packets
                continue

            tags = {"host": packet.hostname}

            try:
                cluster_name = self._lookup_cluster_name(packet.sender_host)
                tags["cluster"] = cluster_name
                log.debug("looked up cluster name: %s", cluster_name)
            except Exception as e:
                log.warning("failed to lookup cluster name: %s", e)

            json_body = [
                {
                    "measurement": "gmond",
                    "tags": tags,
                    # "time": "2009-11-10T23:00:00Z",
                    "fields": {packet.metric_name: packet.value},
                }
            ]
            try:
                if self.diag:
                    print(json_body)
                else:
                    self._influx_client.write_points(json_body)
            except Exception as e:
                log.warning("write to InfluxDB failed: %s", e)
