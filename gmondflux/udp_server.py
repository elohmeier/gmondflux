import logging
from gevent.queue import Queue
from gevent.server import DatagramServer

from gmondflux.gmetric_parser import gmetric_parse, GMetricPacket

log = logging.getLogger(__name__)


class PacketQueue(Queue):
    def get(self, block=True, timeout=None) -> GMetricPacket:
        return super().get(block, timeout)


class GmondReceiver(DatagramServer):
    def __init__(self, *args, queue: PacketQueue, **kwargs):
        self.queue = queue
        super().__init__(*args, **kwargs)

    def handle(self, data, address):
        try:
            packet = gmetric_parse(data)
            if packet.is_metadata():
                return  # skip metadata packets as early as possible
            packet.set_sender(address)
            packet.set_timestamp()
            self.queue.put(packet)
        except Exception as e:
            log.debug("could not parse udp packet: %s", e)
