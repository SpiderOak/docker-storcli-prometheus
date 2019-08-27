What This Is
============

It's a script to pull RAID status from various RAID clients (storcli, megacli, perccli),
and write them in Prometheus-compatible output somewhere.

You can make `prometheus-node-exporter` pull these in as textfiles,
and then you have RAID stuff in prometheus.
We use this to monitor drive failure, mostly.

Installing
----------

On a Debian-based system (including Ubuntu):

``` sh
sudo apt install prometheus-node-exporter moreutils
sudo sed -i "s#^ARGS='#ARGS='-collector.textfile.directory=/var/lib/node-exporter #" /etc/defaults/prometheus-node-exporter
sudo systemctl restart prometheus-node-exporter
cd /usr/local/src && sudo git clone https://github.com/nealey/docker-storcli-prometheus
cat <<EOD | sudo tee /etc/cron.d/prometheus-storcli > /dev/null
*/5 * * * * root python /usr/local/src/docker-storcli-prometheus/storcli.py --storcli_path=/opt/MegaRAID/perccli/perccli64 | sponge /var/lib/node-exporter/perccli.prom
*/5 * * * * root python /usr/local/src/docker-storcli-prometheus/storcli.py --storcli_path=/opt/MegaRAID/storcli/storcli64 | sponge /var/lib/node-exporter/storcli.prom
*/5 * * * * root python /usr/local/src/docker-storcli-prometheus/storcli.py --storcli_path=/opt/MegaRAID/megacli/megacli64 | sponge /var/lib/node-exporter/megacli.prom
EOD
```

This will run, every 5 minutes, something to probe every known (to me) RAID controller type,
and output data to the node-exporter.

You will probably get errors if you just paste this in.
At the very least you should delete the cron entries for binaries you don't have installed.
