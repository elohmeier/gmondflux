import datetime

from carbon2influx import parse_carbon

# graphite_prefix, cluster_name, host_name, metric_name, value, timestamp


def test_local_sample():
    msg = b"nw30.gmetad.unspecified.localhost.bytes_out 4693.38 1554733272\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "bytes_out"
    assert res[4] == "4693.38"
    assert res[5] == datetime.datetime(2019, 4, 8, 14, 21, 12)


def test_old_sample_value():
    msg = b"nw30.gmetad.unspecified.localhost.mem_cached\n 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "mem_cached"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_spaced_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_total_size of Uncompressed Pool\n 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_total_size of Uncompressed Pool"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_even_more_spaced_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_total_size of Uncompressed Pool  1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_total_size of Uncompressed Pool"
    assert res[4] == ""
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_hyphen_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_free_absolute_opt-av 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_free_absolute_opt-av"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_dollar_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_free_ab$olute_opt-av 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_free_ab$olute_opt-av"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_slash_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_free_absolute_opt-av I/O 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_free_absolute_opt-av I/O"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_tilde_value():
    msg = b"nw30.gmetad.unspecified.localhost.disk_free_absolute_opt~secret-oauth-cfg 740328 1553601594\n"
    res = parse_carbon(msg)
    assert res[0] == "nw30.gmetad"
    assert res[1] == "unspecified"
    assert res[2] == "localhost"
    assert res[3] == "disk_free_absolute_opt~secret-oauth-cfg"
    assert res[4] == "740328"
    assert res[5] == datetime.datetime(2019, 3, 26, 11, 59, 54)


def test_real_world_empty_sample():
    msg = b"srsmel100.server.debeka.de.gmetad.P8B_RZA.srappu013-adm_server_debeka_de.hdisk0_max_wserv  1554735743\n"
    res = parse_carbon(msg)
    assert res[0] == "srsmel100.server.debeka.de.gmetad"
    assert res[1] == "P8B_RZA"
    assert res[2] == "srappu013-adm_server_debeka_de"
    assert res[3] == "hdisk0_max_wserv"
    assert res[4] == ""
    assert res[5] == datetime.datetime(2019, 4, 8, 15, 2, 23)


def test_real_world_has_dots_sample():
    msg = b"srsmel100.server.debeka.de.gmetad.P8B_RZA.srappu013-adm_server_debeka_de.kubernetes.io-1234-hdisk0_max_wserv 1234 1554735743\n"
    res = parse_carbon(msg)
    assert res[0] == "srsmel100.server.debeka.de.gmetad"
    assert res[1] == "P8B_RZA"
    assert res[2] == "srappu013-adm_server_debeka_de"
    assert res[3] == "kubernetes.io-1234-hdisk0_max_wserv"
    assert res[4] == "1234"
    assert res[5] == datetime.datetime(2019, 4, 8, 15, 2, 23)


def test_real_world_has_strange_characters_sample():
    msg = b"srsmel100.server.debeka.de.gmetad.P8C_RZB.srvspu022-adm_server_debeka_de.hdisk0_xfers \xea\xef)\xf0\xf4\x7f 1554735743\n"
    res = parse_carbon(msg)
    assert res[0] == "srsmel100.server.debeka.de.gmetad"
    assert res[1] == "P8C_RZB"
    assert res[2] == "srvspu022-adm_server_debeka_de"
    assert res[3] == "hdisk0_xfers"
    assert res[4] == ""
    assert res[5] == datetime.datetime(2019, 4, 8, 15, 2, 23)


def test_real_world_has_percent_characters_sample():
    msg = b"srsmel100.server.debeka.de.gmetad.P8C_RZB.srvspu022-adm_server_debeka_de.hdisk0v1%27_xfers 1234 1554735743\n"
    res = parse_carbon(msg)
    assert res[0] == "srsmel100.server.debeka.de.gmetad"
    assert res[1] == "P8C_RZB"
    assert res[2] == "srvspu022-adm_server_debeka_de"
    assert res[3] == "hdisk0v1%27_xfers"
    assert res[4] == "1234"
    assert res[5] == datetime.datetime(2019, 4, 8, 15, 2, 23)
