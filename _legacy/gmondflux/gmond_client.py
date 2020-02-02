import socket
import xml.sax


class GangliaContentHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        super().__init__()
        self.cluster_name = None

    def startElement(self, name, attrs):
        if name == "CLUSTER":
            self.cluster_name = attrs.getValue("NAME")


def read_cluster_name(host, port):
    handler = GangliaContentHandler()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)  # wait max. 1 second
        s.connect((host, port))
        while True:
            buffer = s.recv(1024)
            parser.feed(buffer)
            if buffer == b"":
                break

        s.close()

    return handler.cluster_name
