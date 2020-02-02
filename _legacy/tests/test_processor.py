from gmondflux.processor import split_metric


def test_no_split():
    extra_tags, field_name = split_metric("disk_write")
    assert len(extra_tags) == 0
    assert field_name == "disk_write"


def test_ent_split():
    extra_tags, field_name = split_metric("ent0_bytes_received")
    assert len(extra_tags) == 1
    assert extra_tags["interface"] == "ent0"
    assert field_name == "bytes_received"


def test_conversion():
    val = b"95"
    assert float(val) == 95
