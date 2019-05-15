import time

from xdrlib import Unpacker

_slope_int2str = {0: "zero", 1: "positive", 2: "negative", 3: "both", 4: "unspecified"}


class GMetricPacket:
    def __init__(self, packet_type, hostname, metric_name, spoof):
        self.spoof = spoof
        self.metric_name = metric_name
        self.hostname = hostname
        self.packet_type = packet_type
        self.type_representation = None
        self.units = None
        self.slope = None
        self.tmax = None
        self.dmax = None
        self.extra_data = {}
        self.printf = None
        self.value = None
        self.sender_host = None
        self.timestamp = None

    def set_sender(self, address):
        assert len(address) == 2, "invalid address"
        assert isinstance(address[0], str)
        self.sender_host = address[0]

    def set_timestamp(self):
        self.timestamp = time.time()

    def is_metadata(self):
        return self.packet_type == 128


def gmetric_parse(msg) -> GMetricPacket:
    unpacker = Unpacker(msg)
    packet_type = unpacker.unpack_int()

    if packet_type not in (128, 129, 131, 132, 133, 134, 135):
        raise NotImplementedError("packet_type %s unsupported" % packet_type)

    hostname = unpacker.unpack_string().decode()
    metric_name = unpacker.unpack_string().decode()
    spoof = unpacker.unpack_uint()

    packet = GMetricPacket(packet_type, hostname, metric_name, spoof)

    if packet_type == 128:
        packet.type_representation = unpacker.unpack_string().decode()
        packet.metric_name = unpacker.unpack_string().decode()
        packet.units = unpacker.unpack_string().decode()
        packet.slope = _slope_int2str[unpacker.unpack_int()]
        packet.tmax = unpacker.unpack_uint()
        packet.dmax = unpacker.unpack_uint()
        extra_data_qualifier = unpacker.unpack_uint()

        for i in range(0, extra_data_qualifier):
            name = unpacker.unpack_string().decode()
            value = unpacker.unpack_string().decode()
            packet.extra_data[name] = value

    if packet_type != 128:
        packet.printf = unpacker.unpack_string().decode()

    if packet_type == 129:
        packet.value = unpacker.unpack_uint()
    if packet_type == 131:
        packet.value = unpacker.unpack_int()
    if packet_type == 132:
        packet.value = unpacker.unpack_int()
    if packet_type == 133:
        packet.value = unpacker.unpack_string()
    if packet_type == 134:
        packet.value = unpacker.unpack_float()
    if packet_type == 135:
        packet.value = unpacker.unpack_double()

    unpacker.done()

    return packet
