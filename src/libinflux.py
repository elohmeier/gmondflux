from datetime import datetime

import base64
import logging
import re
import urllib2

log = logging.getLogger(__name__)
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
    if isinstance(value, str):
        value = value.decode("utf-8")

    elif isinstance(value, int) and not isinstance(value, bool):
        return str(value) + "i"
    elif _is_float(value):
        return repr(value)

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
        req = urllib2.Request(url=url, data=data)
        if username and password:
            auth = base64.b64encode("%s:%s" % (username, password))
            req.add_header("Authorization", "Basic %s" % auth)
        res = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        log.error("data transmission to InfluxDB failed: %s", e)
        log.error(e.read())
        log.error(data)
        return
    if res.code == 204:
        log.info("transmission succeeded, HTTP-Status %s", res.code)
    else:
        log.error("transmission failed, HTTP-Status %s", res.code)


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
    fieldname = fieldname.strip().replace(" ", "\\ ")
    if fieldname == "time":
        return "gtime"
    return fieldname
