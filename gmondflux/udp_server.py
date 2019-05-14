import logging
from gevent.server import DatagramServer

from gmondflux.gmetric_parser import gmetric_read

log = logging.getLogger(__name__)


class GmondReceiver(DatagramServer):
    def __init__(self, *args, **kwargs):
        self.queue = kwargs.pop("queue")
        super().__init__(*args, **kwargs)

    def handle(self, data, address):
        try:
            m = gmetric_read(data)
            self.queue.append(m)
        except Exception as e:
            log.debug("could not parse udp packet: %s", e)
