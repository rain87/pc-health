#!/usr/bin/python

import rrd_config as C
import re
import subprocess
import os
import sys

devices = set(C.network_devices)

if len(sys.argv) > 1 and sys.argv[1] == 'reset':
    def reset_stat(dev):
        assert subprocess.Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'traffic_{dev}.rrd'.format(dev=dev)),
            '--template', ':'.join(C.Traffic._fields), '--',
            'N' + ':U' * len(C.Traffic._fields)]).wait() == 0
    map(reset_stat, devices)
    sys.exit(0)

#                      1       2                         3              4           5
rx = re.compile('^\s*(\d+)\s+(\d+)\s+(?:ACCEPT|)\s+(tcp|udp|all).*(tun\d|eth\d).*?(NEW|)$')
input = dict()
output = dict()
target = None

iptables = subprocess.Popen(['sudo', 'iptables', '-xnvL'], stdout=subprocess.PIPE)
#iptables = subprocess.Popen(['cat', 'test_ipt'], stdout=subprocess.PIPE)
while True:
    line = iptables.stdout.readline()
    if not line:
        break
    if line.startswith('Chain INPUT'):
        target = input
        continue
    if line.startswith('Chain OUTPUT'):
        target = output
        continue
    m = rx.match(line)
    if not m:
        continue
    dev = m.group(4)
    if not dev in target:
        target[dev] = []
    target[dev].append([m.group(i) for i in [1, 2, 3, 5]])

assert set(input.keys()) == devices
assert set(output.keys()) == devices

def get_traffic(input, output):
    kw = dict()
    def pack_values(v, direction):
        if v[3]:
            kw["{proto}_new_{direction}".format(proto=v[2], direction=direction)] = v[0]
        else:
            kw["{proto}_bytes_{direction}".format(proto=v[2], direction=direction)] = v[1]
            kw["{proto}_pckts_{direction}".format(proto=v[2], direction=direction)] = v[0]

    map(lambda values: pack_values(values, 'in'), input)
    map(lambda values: pack_values(values, 'out'), output)
    return C.Traffic(**kw)

for dev in input.keys():
    assert subprocess.Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'traffic_{dev}.rrd'.format(dev=dev)),
        '--template', ':'.join(C.Traffic._fields), '--',
        'N:' + ':'.join(get_traffic(input[dev], output[dev]))]).wait() == 0
