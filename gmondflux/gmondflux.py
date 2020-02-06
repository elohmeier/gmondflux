#!/usr/bin/env python3

import argparse
import logging
import socket
import sys
import time

from xdrlib import Unpacker

logger = logging.getLogger("gmondflux")

udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
telegraf_client = None
telegraf_socket_path = None

# in seconds. used to buffer the "socket does not exist" messages
COMPLAINT_FREQUENCY = 60

# allow early "socket does not exist" messages
last_socket_complaint = time.time() - COMPLAINT_FREQUENCY


def _iql_escape_tag(tag):
    return (
        tag.replace("\\", "\\\\")
        .replace(" ", "\\ ")
        .replace(",", "\\,")
        .replace("=", "\\=")
        .replace("\n", "\\n")
    )


def _iql_escape_tag_value(value):
    ret = _iql_escape_tag(value)
    if ret.endswith("\\"):
        ret += " "
    return ret


_slope_int2str = {0: "zero", 1: "positive", 2: "negative", 3: "both", 4: "unspecified"}


class GmondPacket:
    def __init__(self, raw_data):
        unpacker = Unpacker(raw_data)
        self.packet_type = unpacker.unpack_int()

        if self.packet_type not in (128, 129, 131, 132, 133, 134, 135):
            raise NotImplementedError("packet_type %s unsupported" % self.packet_type)

        self.hostname = unpacker.unpack_string().decode()
        if ":" in self.hostname:
            self.ip_address, self.hostname = self.hostname.split(":")
        self.metric_name = unpacker.unpack_string().decode()
        self.spoof = unpacker.unpack_uint()

        if self.is_metadata_packet:
            self.type_representation = unpacker.unpack_string().decode()
            self.metric_name = unpacker.unpack_string().decode()
            self.units = unpacker.unpack_string().decode()
            self.slope = _slope_int2str[unpacker.unpack_int()]
            self.tmax = unpacker.unpack_uint()
            self.dmax = unpacker.unpack_uint()
            self.value = None
            extra_data_qualifier = unpacker.unpack_uint()

            self.extra_data = {}
            for i in range(0, extra_data_qualifier):
                name = unpacker.unpack_string().decode()
                value = unpacker.unpack_string().decode()
                self.extra_data[name] = value
        else:
            self.printf = unpacker.unpack_string().decode()

        if self.packet_type == 129:
            self.value = unpacker.unpack_uint()
            self.value_iql = str(self.value) + "i"
        if self.packet_type == 131:
            self.value = unpacker.unpack_int()
            self.value_iql = str(self.value) + "i"
        if self.packet_type == 132:
            self.value = unpacker.unpack_int()
            self.value_iql = str(self.value) + "i"
        if self.packet_type == 133:
            self.value = unpacker.unpack_string().decode()
            self.value_iql = '"{}"'.format(
                self.value.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
            )
        if self.packet_type == 134:
            self.value = unpacker.unpack_float()
            self.value_iql = repr(self.value)
        if self.packet_type == 135:
            self.value = unpacker.unpack_double()
            self.value_iql = repr(self.value)

        if not self.is_metadata_packet:
            logger.debug('converted "%s" to "%s" (IQL)', self.value, self.value_iql)

        unpacker.done()

    @property
    def is_metadata_packet(self):
        return self.packet_type == 128

    def iql(self):
        if self.is_metadata_packet:
            raise NotImplementedError("Metadata packets cannot be converted to IQL.")

        return "gmond,host={} {}={}\n".format(
            _iql_escape_tag_value(self.hostname), self.metric_name, self.value_iql
        )

    def __repr__(self):
        return "GmondPacket(%s, %s, %s, %s)" % (
            self.packet_type,
            self.hostname,
            self.metric_name,
            self.value,
        )


def configure_listener(udp_listen_address, udp_listen_port):
    udp_server.bind((udp_listen_address, udp_listen_port))
    logger.info(
        "listening for UDP traffic on %s:%s", udp_listen_address, udp_listen_port
    )


def telegraf_send(packet):
    global telegraf_client, last_socket_complaint
    iql = packet.iql()
    logger.debug("generated IQL: %s", iql)

    if telegraf_client is None:
        logger.debug("trying to connect to telegraf socket")
        try:
            telegraf_client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            telegraf_client.connect(telegraf_socket_path)
            logger.info("bound to telegraf socket: %s", telegraf_socket_path)
        except FileNotFoundError:
            if last_socket_complaint < (time.time() - COMPLAINT_FREQUENCY):
                logger.warning(
                    'Telegraf socket "%s" does not exist.' % telegraf_socket_path
                )
                last_socket_complaint = time.time()
            telegraf_client.close()
            telegraf_client = None

    if telegraf_client is not None:
        try:
            telegraf_client.send(iql.encode())
            logger.debug("packet forwarded to telegraf.")
            return
        except BrokenPipeError:
            logger.warning("Telegraf socket has been closed.")
            telegraf_client.close()
            telegraf_client = None
        except Exception:
            logger.exception("failed to forward packet to telegraf.")

    logger.debug("packet dropped.")


def recv_packet():
    data, address = udp_server.recvfrom(4096)  # maximum packet size was guessed
    logger.debug("packet received.")
    packet = GmondPacket(data)
    logger.debug("parsed packet: %s", packet)
    return packet


def process_events():
    while True:
        try:
            packet = recv_packet()
        except Exception:
            logger.warning(
                "failed to receive/parse packet, skipping it.", exc_info=True
            )
            continue

        if not packet.is_metadata_packet:
            telegraf_send(packet)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Listens for Ganglia gmond metrics on UDP and writes them to a Telegraf socket, using the InfluxDB line protocol. https://git.nerdworks.de/nerdworks/gmondflux"
    )

    parser.add_argument(
        "-a",
        "--listen-address",
        default="0.0.0.0",
        help="the IPv4 address to listen on for gmond traffic, default is 0.0.0.0 (listen on all interfaces).",
    )
    parser.add_argument(
        "-p",
        "--listen-port",
        type=int,
        default=8679,
        help="the port to listen on for gmond traffic, default is 8679.",
    )
    parser.add_argument(
        "-t",
        "--telegraf-socket",
        default="/tmp/telegraf.sock",
        help="Telegraf socket to send metrics to, default is /tmp/telegraf.sock.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help="increase log output verbosity level. E.g. -v for DEBUG.",
    )

    args = parser.parse_args()

    args.verbose = (
        30 - (10 * args.verbose) if args.verbose > 0 else 0
    )  # default level: INFO
    logging.basicConfig(stream=sys.stderr, level=args.verbose)

    configure_listener(args.listen_address, args.listen_port)
    telegraf_socket_path = args.telegraf_socket

    try:
        process_events()
    except KeyboardInterrupt:
        logger.info("shutting down...")
    finally:
        udp_server.close()
        if telegraf_client is not None:
            telegraf_client.close()
