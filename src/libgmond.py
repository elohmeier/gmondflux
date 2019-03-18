import logging
from xdrlib import Unpacker

log = logging.getLogger(__name__)

_slope_int2str = {0: "zero", 1: "positive", 2: "negative", 3: "both", 4: "unspecified"}


def gmetric_read(msg):
    unpacker = Unpacker(msg)
    values = dict()
    packet_type = unpacker.unpack_int()
    values["packet_type"] = packet_type

    if packet_type in (128, 129, 131, 132, 133, 134, 135):
        values["hostname"] = unpacker.unpack_string()
        values["metric_name"] = unpacker.unpack_string()
        values["spoof"] = unpacker.unpack_uint()
    else:
        raise NotImplementedError("packet_type %s unsupported" % packet_type)

    if packet_type == 128:
        log.debug("### METADATA PACKET (type %s) ###", packet_type)
        values["type_representation"] = unpacker.unpack_string()
        values["metric_name"] = unpacker.unpack_string()
        values["units"] = unpacker.unpack_string()
        values["slope"] = _slope_int2str[unpacker.unpack_int()]
        values["tmax"] = unpacker.unpack_uint()
        values["dmax"] = unpacker.unpack_uint()
        values["extra_data"] = {}
        extra_data_qualifier = unpacker.unpack_uint()

        for i in range(0, extra_data_qualifier):
            name = unpacker.unpack_string()
            value = unpacker.unpack_string()
            values["extra_data"][name] = value

    if packet_type != 128:
        log.debug("### VALUE PACKET (type %s) ###", packet_type)
        values["printf"] = unpacker.unpack_string()

    if packet_type == 129:
        values["value"] = unpacker.unpack_uint()
    if packet_type == 131:
        values["value"] = unpacker.unpack_int()
    if packet_type == 132:
        values["value"] = unpacker.unpack_int()
    if packet_type == 133:
        values["value"] = unpacker.unpack_string()
    if packet_type == 134:
        values["value"] = unpacker.unpack_float()
    if packet_type == 135:
        values["value"] = unpacker.unpack_double()

    log.debug(values)
    try:
        unpacker.done()
    except Exception as e:
        log.error(e)
        log.error("position: %s / %s", unpacker.get_position(), len(msg))
        log.error(unpacker.get_buffer())
    return packet_type, values


class GmondGroupie(object):
    def __init__(self):
        self.metric_groups = {}

    def learn_meta(self, values):
        if not is_meta(values["packet_type"]):  # ignore non-metadata packets
            return

        self.metric_groups[values["metric_name"]] = values["extra_data"]["GROUP"]

    def get_group(self, metric_name):
        if metric_name not in self.metric_groups:
            log.warning("metric %s is not known from metadata (yet)", metric_name)
            return None
        return self.metric_groups[metric_name]


def is_meta(packet_type):
    return packet_type == 128
