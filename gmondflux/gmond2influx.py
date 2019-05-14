#!/usr/bin/python2
from __future__ import unicode_literals
from __future__ import with_statement

import sys
from datetime import datetime

import argparse
import base64
import logging
import re
import socket
import threading

from gmondflux.gmetric_parser import gmetric_read

try:
    from urllib2 import urlopen, Request, HTTPError, URLError
except ImportError:
    from urllib.request import urlopen, Request
    from urllib.error import HTTPError, URLError

log = logging.getLogger(__name__)


class GmondGroupie(object):
    def __init__(self):
        self.metric_groups = {}

    def learn_meta(self, values):
        if not is_meta(values["packet_type"]):  # ignore non-metadata packets
            return

        self.metric_groups[values["metric_name"]] = values["extra_data"]["GROUP"]

    def get_group(self, metric_name):
        if metric_name not in self.metric_groups:
            log.debug("metric %s is not known from metadata (yet)", metric_name)
            return None
        return self.metric_groups[metric_name]


def is_meta(packet_type):
    return packet_type == 128


EPOCH = datetime.utcfromtimestamp(0)


def _is_float(value):
    try:
        float(value)
    except (TypeError, ValueError):
        return False

    return True


def quote_ident(value):
    """Indent the quotes."""
    return '"{}"'.format(
        value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    )


def _escape_value(value):
    if (sys.version[0] == 2 and isinstance(value, str)) or (
        sys.version[0] == 3 and isinstance(value, bytes)
    ):
        value = value.decode("utf-8")
    elif isinstance(value, int) and not isinstance(value, bool):
        return str(value) + "i"
    elif _is_float(value):
        return repr(float(value))

    return quote_ident(value)


def build_influxql(measurement_name, tag_set, field_set, timestamp=None):
    tag_line = ",".join(["%s=%s" % (safe_fieldname(k), v) for k, v in tag_set.items()])
    field_line = ",".join(
        ["%s=%s" % (safe_fieldname(k), _escape_value(v)) for k, v in field_set.items()]
    )
    if timestamp:
        timestamp_nanoseconds = int((timestamp - EPOCH).total_seconds() * 1e9)
        return "%s,%s %s %s\n" % (
            measurement_name,
            tag_line,
            field_line,
            timestamp_nanoseconds,
        )
    return "%s,%s %s\n" % (measurement_name, tag_line, field_line)


def transmit(url, username, password, data):
    log.debug("transferring data to %s", url)
    try:
        req = Request(url=url, data=data.encode("utf-8"))
        if username and password:
            auth = base64.b64encode(("%s:%s" % (username, password)).encode("utf-8"))
            req.add_header("Authorization", b"Basic " + auth)
        res = urlopen(req)
    except HTTPError as e:
        log.error("data transmission to InfluxDB failed: %s", e)
        log.debug(e.read())
        log.debug(data)
        return False
    except URLError as e:
        log.error("data transmission to InfluxDB failed: %s", e)
        log.debug(data)
        return False
    if res.code == 204:
        log.debug("transmission succeeded, HTTP-Status %s", res.code)
        return True
    else:
        log.error("transmission failed, HTTP-Status %s", res.code)
        return False


def split_by_prefix(
    tag_set,
    field_set,
    tag_name,
    prefix_pattern=r"^([A-Za-z0-9]+)[-_](.*)$",
    new_prefix="",
):

    prefixed_field_set = {}
    unprefixed_field_set = {}

    for field_key in field_set:
        # log.debug("field_key: %s", field_key)
        m = re.match(prefix_pattern, field_key)
        if m:
            prefix = m.group(1)
            # log.debug("prefix %s detected", prefix)
            if prefix not in prefixed_field_set:
                prefixed_field_set[prefix] = {}
            prefixed_field_set[prefix][new_prefix + m.group(2)] = field_set[field_key]
        else:
            # log.debug("no prefix detected")
            unprefixed_field_set[field_key] = field_set[field_key]

    if any(unprefixed_field_set):
        # log.debug("yielding unprefixed field_set %s, tags: %s", unprefixed_field_set, tag_set)
        yield tag_set, unprefixed_field_set

    for prefix, field_set in prefixed_field_set.items():
        tag_set = tag_set.copy()
        tag_set[tag_name] = prefix
        # log.debug("yielding prefixed field_set %s, tags: %s", field_set, tag_set)
        yield tag_set, field_set


def safe_fieldname(fieldname):
    fieldname = fieldname.strip().replace(" ", "\\ ").replace(",", "\\,")
    if fieldname == "time":
        return "gtime"
    return fieldname


class ItemStore(object):
    def __init__(self, max_length=10000):
        self.max_length = max_length
        self.wakeup = threading.Condition()
        self.shutdown_flag = threading.Event()
        self.items = []

    def add(self, item):
        with self.wakeup:
            if 0 < self.max_length < len(self.items):
                log.debug("ItemStore is full")
                return
            self.items.append(item)
            self.wakeup.notify()  # wake 1 thread

    def get_all(self):
        with self.wakeup:
            while (
                not self.shutdown_flag.is_set() and len(self.items) == 0
            ):  # return at least 1 item
                self.wakeup.wait()
            items, self.items = self.items, []
        return items


class ProcessInfluxQueueJob(threading.Thread):
    def __init__(self, influx_url, username, password, store, diag_only):
        super(ProcessInfluxQueueJob, self).__init__()
        self.diag_only = diag_only
        self.store = store
        self.password = password
        self.username = username
        self.influx_url = influx_url
        self.groupie = GmondGroupie()

    def run(self):
        while not self.store.shutdown_flag.is_set():
            items = self.store.get_all()
            if len(items) == 0:
                continue

            log.debug("processing %s items", len(items))
            iql = ""

            for timestamp, data in items:
                try:
                    packet_type, values = gmetric_read(data)
                except Exception as e:
                    log.error("parsing packet failed: %s", e)
                    continue

                if is_meta(packet_type):
                    self.groupie.learn_meta(values)
                    continue

                group = self.groupie.get_group(values["metric_name"])
                if not group:
                    log.debug("skipping non-groupable value packet")
                    continue

                tag_set = {"host": values["hostname"]}
                field_set = {values["metric_name"]: values["value"]}

                split_groups = {
                    "aixdisk": "device",
                    "ibmfc": "device",
                    "ibmnet": "interface",
                }

                if group in split_groups:
                    for tag_set, field_set in split_by_prefix(
                        tag_set, field_set, split_groups[group]
                    ):
                        iql += build_influxql(
                            measurement_name=group,
                            tag_set=tag_set,
                            field_set=field_set,
                            # timestamp=timestamp,
                        )
                else:
                    iql += build_influxql(
                        measurement_name=group,
                        tag_set=tag_set,
                        field_set=field_set,
                        # timestamp=timestamp,
                    )

            if iql != "":
                if self.diag_only:
                    sys.stdout.write(iql)
                else:
                    transmit(self.influx_url, self.username, self.password, iql)


def listen_udp(listen_address, listen_port, store):
    log.info("listening for UDP traffic on %s:%s", listen_address, listen_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_address, listen_port))
    while True:
        data, address = sock.recvfrom(4096)  # maximum packet size was guessed
        log.debug("received %s bytes from %s", len(data), address)
        timestamp = datetime.now()
        store.add((timestamp, data))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-a",
        "--listen-address",
        default="0.0.0.0",
        help="the IPv4 address to listen on for gmond traffic, default is 0.0.0.0 (listen on all interfaces)",
    )
    parser.add_argument(
        "-b",
        "--listen-port",
        type=int,
        default=8679,
        help="the port to listen on for gmond traffic, default is 8679",
    )
    parser.add_argument(
        "-s",
        "--server-url",
        default="https://srsmvl007.server.debeka.de:8086/write?db=gmond",
        help="URL of the target InfluxDB instance, HTTPS is required. default is 'https://srsmvl007.server.debeka.de:8086/write?db=gmond'",
    )
    parser.add_argument(
        "-u", "--username", help="username used for authentication against InfluxDB"
    )
    parser.add_argument(
        "-p", "--password", help="password used for authentication against InfluxDB"
    )
    parser.add_argument(
        "-d",
        "--diag",
        help="don't send any data just print the data to STDOUT which would be sent to InfluxDB",
        action="store_true",
    )
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )

    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    s = ItemStore()
    t = ProcessInfluxQueueJob(
        args.server_url, args.username, args.password, s, args.diag
    )
    t.start()
    log.debug("started ProcessInfluxQueueJob thread")

    try:
        listen_udp(args.listen_address, args.listen_port, s)
    except socket.error as e:
        log.error("error initializing UDP-Listener: %s", e)
        exit(1)
    except KeyboardInterrupt:
        log.info("shutting down")
    finally:
        log.debug("shutting down ProcessInfluxQueueJob thread")
        s.shutdown_flag.set()
        with s.wakeup:
            s.wakeup.notify()
        t.join()
