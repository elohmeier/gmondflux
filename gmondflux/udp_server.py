from gevent.server import DatagramServer


class GmondReceiver(DatagramServer):

    def handle(self, data, address):
        print("got smth", address, data)
