from xdrlib import Unpacker

_slope_int2str = {0: "zero", 1: "positive", 2: "negative", 3: "both", 4: "unspecified"}


def gmetric_read(msg):
    unpacker = Unpacker(msg)
    values = dict()
    packet_type = unpacker.unpack_int()
    values["packet_type"] = packet_type

    if packet_type in (128, 129, 131, 132, 133, 134, 135):
        values["hostname"] = unpacker.unpack_string().decode()
        values["metric_name"] = unpacker.unpack_string().decode()
        values["spoof"] = unpacker.unpack_uint()
    else:
        raise NotImplementedError("packet_type %s unsupported" % packet_type)

    if packet_type == 128:
        values["type_representation"] = unpacker.unpack_string().decode()
        values["metric_name"] = unpacker.unpack_string().decode()
        values["units"] = unpacker.unpack_string().decode()
        values["slope"] = _slope_int2str[unpacker.unpack_int()]
        values["tmax"] = unpacker.unpack_uint()
        values["dmax"] = unpacker.unpack_uint()
        values["extra_data"] = {}
        extra_data_qualifier = unpacker.unpack_uint()

        for i in range(0, extra_data_qualifier):
            name = unpacker.unpack_string().decode()
            value = unpacker.unpack_string().decode()
            values["extra_data"][name] = value

    if packet_type != 128:
        values["printf"] = unpacker.unpack_string().decode()

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

    unpacker.done()

    return values
