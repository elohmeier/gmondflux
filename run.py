import gevent.monkey; gevent.monkey.patch_all()
import logging
from influxdb import InfluxDBClient

from gmondflux.processor import MessageProcessor



from gevent.queue import Queue

from gmondflux.udp_server import GmondReceiver


logging.basicConfig(level=logging.DEBUG)


if __name__ == "__main__":
    print("starting up...")

    q = Queue()
    r = GmondReceiver(":8649", queue=q)

    c = InfluxDBClient(port=18086)

    p = MessageProcessor(q, c)
    p.start()

    try:
        r.serve_forever()
    except KeyboardInterrupt:
        print("shutting down...")
