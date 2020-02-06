# gmondflux

Target Platform is Python 3.4 (SLES 12).

## Testing

1. Start Telegraf Socket Listener using `telegraf --config configs/telegraf.conf`.
2. Start gmondflux using `./gmondflux/gmondflux.py -t telegraf.sock`.
3. Send metrics using `gmetric -c configs/gmetric.conf -n my_metric -t string -v abc`.
4. The metric should be displayed on STDOUT of the Telegraf process.
