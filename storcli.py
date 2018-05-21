#!/usr/bin/env python
"""
Based on storcli.py example from node_exporter, with substantial changes.

https://github.com/prometheus/node_exporter/blob/master/text_collector_examples/storcli.py


megaraid_controllers{controller,model}=1
megaraid_controller_memory_errors{controller,correctable=y|n}=counter
megaraid_controller_bbu{controller}=0|1
megaraid_roc_temp_celcius{controller}=gauge
megaraid_virtual_drives{controller,vd,type,state=optimal|partially|degraded|offline}=1
megaraid_vd_size_bytes{controller,vd}=gauge
megaraid_physical_drives{controller,enclosure,slot,vd,state=online|offline|ugood|ubad|ghs|dhs}=1
megaraid_pd_size_bytes{controller,enclosure,slot}=gauge
"""

from __future__ import print_function
import argparse
import json
import os
import subprocess
import re
from decimal import Decimal

DESCRIPTION = """Parses StorCLI's JSON output and exposes MegaRAID health as
    Prometheus metrics."""
VERSION = '0.0.1'


def parse_size(size):
    n, u = re.match(r'(\d+\.\d+) ([A-Z])B$', size).groups()
    n = Decimal(n)
    for k in 'KMGTPE':
        n *= 1024
        if u == k:
            break
    else:
        raise RuntimeError('unsupported size unit')
    return int(n)


def main(args):
    """ main """

    controllers = []
    vds = []
    pds = []
    data = json.loads(get_storcli_json(args.storcli_path))

    for ctrl in data['Controllers']:
        dg_vd_map = {'-': None}

        resp = ctrl.get('Response Data')
        if not resp:
            continue

        ctrl_id = int(resp['Basics']['Controller'])
        controllers.append({
            'controller': ctrl_id,
            'model': resp['Basics']['Model'],
            'errors_correctable': int(resp['Status']['Memory Correctable Errors']),
            'errors_uncorrectable': int(resp['Status']['Memory Uncorrectable Errors']),
            'bbu': int(resp['HwCfg']['BBU'] != 'Absent'),
            'roc_temp': int(resp['HwCfg']['ROC temperature(Degree Celsius)']),
        })

        for vd in resp['VD LIST']:
            dg, vd_id = map(int, vd['DG/VD'].split('/'))
            dg_vd_map[vd_id] = dg
            vds.append({
                'controller': ctrl_id,
                'vd': vd_id,
                'type': vd['TYPE'],
                'state': vd['State'],
                'size': parse_size(vd['Size']),
            })

        for pd in resp['PD LIST']:
            enc, slot = map(int, pd['EID:Slt'].split(':'))
            pds.append({
                'controller': ctrl_id,
                'enclosure': enc,
                'slot': slot,
                'vd': dg_vd_map.get(pd['DG']),
                'state': pd['State'],
                'size': parse_size(pd['Size']),
            })

    print('# HELP megaraid_controllers MegaRAID controllers')
    print('# TYPE megaraid_controllers gauge')
    for ctrl in controllers:
        print('megaraid_controllers{{controller="{controller}",model="{model}"}} 1'.format(**ctrl))

    print('# HELP megaraid_controller_memory_errors MegaRAID controller memory errors')
    print('# TYPE megaraid_controller_memory_errors counter')
    for ctrl in controllers:
        print('megaraid_controller_memory_errors{{controller="{controller}",correctable="y"}} '
              '{errors_correctable}'.format(**ctrl))
        print('megaraid_controller_memory_errors{{controller="{controller}",correctable="n"}} '
              '{errors_uncorrectable}'.format(**ctrl))

    print('# HELP megaraid_controller_bbu MegaRAID controller BBU presence')
    print('# TYPE megaraid_controller_bbu gauge')
    for ctrl in controllers:
        print('megaraid_controller_bbu{{controller="{controller}"}} {bbu}'.format(**ctrl))

    print('# HELP megaraid_roc_temp_celcius MegaRAID controller ROC temperature')
    print('# TYPE megaraid_roc_temp_celcius gauge')
    for ctrl in controllers:
        print('megaraid_roc_temp_celcius{{controller="{controller}"}} {roc_temp}'.format(**ctrl))

    print('# HELP megaraid_virtual_drives MegaRAID virtual drives')
    print('# TYPE megaraid_virtual_drives gauge')
    for vd in vds:
        print('megaraid_virtual_drives{{controller="{controller}",vd="{vd}",'
              'type="{type}",state="{state}"}} 1'.format(**vd))

    print('# HELP megaraid_vd_size_bytes MegaRAID virtual drive size')
    print('# TYPE megaraid_vd_size_bytes gauge')
    for vd in vds:
        print('megaraid_vd_size_bytes{{controller="{controller}",vd="{vd}"}} {size}'.format(**vd))

    print('# HELP megaraid_physical_drives MegaRAID physical drives')
    print('# TYPE megaraid_physical_drives gauge')
    for pd in pds:
        print('megaraid_physical_drives{{controller="{controller}",enclosure="{enclosure}",'
              'slot="{slot}",vd="{vd}",state="{state}"}} 1'.format(**pd))

    print('# HELP megaraid_pd_size_bytes MegaRAID physical drive size')
    print('# TYPE megaraid_pd_size_bytes gauge')
    for pd in pds:
        print('megaraid_pd_size_bytes{{controller="{controller}",enclosure="{enclosure}",'
              'slot="{slot}"}} {size}'.format(**pd))


def get_storcli_json(storcli_path):
    """Get storcli output in JSON format."""

    # Check if storcli is installed
    if os.path.isfile(storcli_path) and os.access(storcli_path, os.X_OK):
        storcli_cmd = [storcli_path, '/call', 'show', 'all', 'J']
        proc = subprocess.Popen(storcli_cmd, shell=False,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output_json = proc.communicate()[0]
    else:
        output_json = (
            '{"Controllers":[{"Command Status": {"Status": "Failure", '
            '"Description": "No Controller found"}}]}'
        )

    return output_json


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser(description=DESCRIPTION,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    PARSER.add_argument('--storcli_path',
                        default='/usr/sbin/storcli',
                        help='path to StorCLi binary')
    PARSER.add_argument('--version',
                        action='version',
                        version='%(prog)s {}'.format(VERSION))
    ARGS = PARSER.parse_args()

    main(ARGS)
