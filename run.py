import gevent.monkey

gevent.monkey.patch_all()

import argparse

import urllib3
from logging import handlers
from pathlib import Path


import logging
from influxdb import InfluxDBClient

from gmondflux.processor import MessageProcessor

from gmondflux.udp_server import GmondReceiver, PacketQueue

log = logging.getLogger(__name__)


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
        "-gx",
        "--gmond-xml-port",
        type=int,
        default=8649,
        help="tcp accept port to fetch XML metadata from gmond sender, default is 8649",
    )
    parser.add_argument(
        "-ia",
        "--influx-host",
        default="localhost",
        help="host of the InfluxDB instance to connect to, default is localhost",
    )
    parser.add_argument(
        "-ib",
        "--influx-port",
        type=int,
        default=8086,
        help="port of the InfluxDB instance to connect to, default is 8086",
    )
    parser.add_argument(
        "-is",
        "--influx-ssl",
        help="use HTTPS to connect to InfluxDB instead of HTTP",
        action="store_true",
    )
    parser.add_argument(
        "-isv",
        "--influx-ssl-verify",
        help="verify SSL certificate against CA when connecting to InfluxDB",
        action="store_true",
    )
    parser.add_argument(
        "-id",
        "--influx-database",
        default="gmond",
        help="database on the InfluxDB instance to insert metrics into, default is gmond",
    )
    parser.add_argument(
        "-iu",
        "--influx-username",
        help="username used for authentication against InfluxDB",
    )
    parser.add_argument(
        "-ip",
        "--influx-password",
        help="password used for authentication against InfluxDB",
    )
    parser.add_argument(
        "-d",
        "--diag",
        help="don't send any data just print the data to STDOUT which would be sent to InfluxDB",
        action="store_true",
    )
    default_log_level = logging.INFO
    parser.add_argument(
        "-ll",
        "--log-level",
        help="set log level (default: INFO), valid options are: DEBUG, INFO, WARNING, ERROR, CRITICAL. smaller means more verbose.",
    )
    parser.add_argument(
        "-ld",
        "--log-dir",
        help="set log directory to store logs, if not set (default) they'll be printed to stdout",
    )

    args = parser.parse_args()
    log_level = args.log_level if args.log_level else default_log_level

    if args.log_dir:
        log_path = Path(args.log_dir)
        log_path.mkdir(exist_ok=True, parents=True)
        fh = handlers.RotatingFileHandler(
            log_path / "gmondflux.log", maxBytes=100 * 1024, backupCount=5
        )
        fh.setLevel(log_level)
        fh.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        log.addHandler(fh)
        log.setLevel(log_level)
    else:
        logging.basicConfig(level=log_level)

    if args.influx_ssl and not args.influx_ssl_verify:
        log.warning(
            "Please use --influx-ssl-verify if possible. You are prone to MITM attacks if you don't."
        )
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    q = PacketQueue()
    r = GmondReceiver(f"{args.listen_address}:{args.listen_port}", queue=q)

    c = InfluxDBClient(
        host=args.influx_host,
        port=args.influx_port,
        username=args.influx_username,
        password=args.influx_password,
        database=args.influx_database,
        ssl=args.influx_ssl,
        verify_ssl=args.influx_ssl_verify,
    )

    p = MessageProcessor(q, c, args.gmond_xml_port, args.diag)
    p.start()

    try:
        log.info(
            "listening for gmond udp traffic on %s:%s...",
            args.listen_address,
            args.listen_port,
        )
        r.serve_forever()
    except KeyboardInterrupt:
        log.info("shutting down...")
