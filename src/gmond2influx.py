#!/usr/bin/python2
from __future__ import with_statement

import sys
from datetime import datetime

import argparse
import logging
import socket
import threading

import libgmond
import libinflux

log = logging.getLogger(__name__)


class ItemStore(object):
    def __init__(self, max_length=10000):
        self.max_length = max_length
        self.wakeup = threading.Condition()
        self.shutdown_flag = threading.Event()
        self.items = []

    def add(self, item):
        with self.wakeup:
            if 0 < self.max_length < len(self.items):
                log.warning("ItemStore is full")
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
        self.groupie = libgmond.GmondGroupie()

    def run(self):
        while not self.store.shutdown_flag.is_set():
            items = self.store.get_all()
            if len(items) == 0:
                continue

            log.debug("processing %s items", len(items))
            iql = ""

            for timestamp, data in items:
                try:
                    packet_type, values = libgmond.gmetric_read(data)
                except Exception as e:
                    log.error("parsing packet failed: %s", e)
                    continue

                if libgmond.is_meta(packet_type):
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
                    for tag_set, field_set in libinflux.split_by_prefix(
                        tag_set, field_set, split_groups[group]
                    ):
                        iql += libinflux.build_influxql(
                            measurement_name=group,
                            tag_set=tag_set,
                            field_set=field_set,
                            # timestamp=timestamp,
                        )
                else:
                    iql += libinflux.build_influxql(
                        measurement_name=group,
                        tag_set=tag_set,
                        field_set=field_set,
                        # timestamp=timestamp,
                    )

            if iql != "":
                if self.diag_only:
                    sys.stdout.write(iql)
                else:
                    libinflux.transmit(
                        self.influx_url, self.username, self.password, iql
                    )


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
    except KeyboardInterrupt:
        log.debug("shutting down ProcessInfluxQueueJob thread")
        s.shutdown_flag.set()
        with s.wakeup:
            s.wakeup.notify()
        t.join()
