# gmondflux

Gmondflux gmond UDP packet receiver.

## Compability

Target Platform is Python 3.4 (SLES 12).

## Configuration

Define tags to extract from the gmond metric name inside `config/gmondflux.json` and pass it to gmondflux.py.
The key-value-pairs will be passed to Pythons re.sub()-function.
The first matching expression will be used.

### example:
```
r"^(?P<hdisk>hdisk\d+)(.*)$" : r"hdisk\2"
hdisk0_max_wserv -> disk_max_wserv
{'disk': 'hdisk0'}
```

## Manual testing

1. Start Telegraf Socket Listener using `telegraf --config configs/telegraf.conf`.
2. Start gmondflux using `./gmondflux/gmondflux.py -t telegraf.sock`.
3. Send metrics using `gmetric -c configs/gmetric.conf -n my_metric -t string -v abc`.
4. The metric should be displayed on STDOUT of the Telegraf process.


## Run automated tests

Execute `pytest --show-capture=no` to run the automated tests. To run this tests, make sure gmetric is in your PATH, e.g. by using the provided [nix-shell](./shell.nix) environment.

