#!/usr/bin/python

import rrd_config as C
import re
import subprocess
import os

tcp_rx = re.compile('\s*(\d+)\s+(\d+)\s+ACCEPT\s+tcp')
udp_rx = re.compile('\s*(\d+)\s+(\d+)\s+ACCEPT\s+udp')
all_rx = re.compile('\s*(\d+)\s+(\d+)\s+ACCEPT\s+all')

tcp = []
udp = []
all = []

def try_match(line, rx, l):
    m = rx.match(line)
    if m:
        l.append((m.group(1), m.group(2)))
        return True
    return False

iptables = subprocess.Popen(['sudo', 'iptables', '-xnvL', '-Z'], stdout=subprocess.PIPE)
while True:
    line = iptables.stdout.readline()
    if not line:
        break
    if try_match(line, tcp_rx, tcp):
        None
    elif try_match(line, udp_rx, udp):
        None
    else:
        try_match(line, all_rx, all)

assert len(tcp) == 2
assert len(udp) == 2
assert len(all) == 2

traf = C.Traffic(tcp[0][1], tcp[1][1], udp[0][1], udp[1][1], all[0][1], all[1][1],
tcp[0][0], tcp[1][0], udp[0][0], udp[1][0], all[0][0], all[1][0])
assert subprocess.Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'traffic.rrd'),
    '--template', ':'.join(traf._fields), '--',
    'N:' + ':'.join(traf)]).wait() == 0
