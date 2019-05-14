import logging
from gevent.queue import Queue
from gevent.server import DatagramServer

from gmondflux.gmetric_parser import gmetric_read

log = logging.getLogger(__name__)


class GmondReceiver(DatagramServer):
    def __init__(self, *args, queue: Queue, **kwargs):
        self.queue = queue
        super().__init__(*args, **kwargs)

    def handle(self, data, address):
        try:
            m = gmetric_read(data)
            self.queue.put((address, m))
        except Exception as e:
            log.debug("could not parse udp packet: %s", e)
