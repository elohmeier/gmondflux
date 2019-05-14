import logging
from gevent import Greenlet
from gevent.queue import Queue
from influxdb import InfluxDBClient

from gmondflux import gmond_client

log = logging.getLogger(__name__)


class MessageProcessor(Greenlet):
    def __init__(self, q: Queue, influx_client: InfluxDBClient, gmond_xml_port=8649):
        super().__init__()
        self._influx_client = influx_client
        self._gmond_xml_port = gmond_xml_port
        self._q = q
        self._cluster_map = {}
        self._host_metric_groups = {}

    def _lookup_cluster_name(self, address):
        host = address[0]

        if host not in self._cluster_map:
            self._cluster_map[host] = gmond_client.read_cluster_name(
                host, self._gmond_xml_port
            )

        return self._cluster_map[host]

    def _run(self):
        while True:
            address, msg = self._q.get()
            log.debug("message from %s: %s", address, msg)

            if msg["packet_type"] == 128:  # metadata packet
                self._learn_group(msg)
                continue

            cluster_name = "none"

            try:
                cluster_name = self._lookup_cluster_name(address)
                log.debug("looked up cluster name: %s", cluster_name)
            except Exception as e:
                log.debug("failed to lookup cluster name: %s", e)

            try:
                group = self._host_metric_groups[msg["hostname"]][msg["metric_name"]]
            except Exception:
                log.debug("group unknown")
                continue

            json_body = [
                {
                    "measurement": group,
                    "tags": {"host": msg["hostname"], "cluster": cluster_name},
                    "time": "2009-11-10T23:00:00Z",
                    "fields": {
                        "Float_value": 0.64,
                        "Int_value": 3,
                        "String_value": "Text",
                        "Bool_value": True,
                    },
                }
            ]
            try:
                self._influx_client.create_database("popo")
                self._influx_client.write_points(json_body, database="popo")
            except Exception as e:
                log.warning("write to InfluxDB failed: %s", e)

    def _learn_group(self, msg):
        host = msg["hostname"]
        metric = msg["metric_name"]
        group = msg["extra_data"]["GROUP"]

        if host not in self._host_metric_groups:
            self._host_metric_groups[host] = {}

        self._host_metric_groups[host][metric] = group

        log.debug("learned %s.%s.%s", host, group, metric)
