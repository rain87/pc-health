#!/usr/bin/python

import re
from collections import namedtuple
from datetime import datetime
import time
import os
from subprocess import Popen
import rrd_config as C

Stat = namedtuple('Stat', ['ts', 'cpu', 'io'])

stats = []

ts_rx = re.compile('(\d\d)/(\d\d)/(\d\d) (\d\d):(\d\d):(\d\d)')
cpu_rx = re.compile('\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')
io_rx = re.compile('(sd\w)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)')

ts = None
cpu = None
io = {}
f = open('/home/rain87/iostat.log', 'rt')
for line in f:
    if ts is None:
        m = ts_rx.match(line)
        if not m:
            continue
        ts = datetime(year=2000 + int(m.group(3)), month=int(m.group(1)), day=int(m.group(2)), hour=int(m.group(4)), minute=int(m.group(5)), second=int(m.group(6)))
        #ts = datetime.strptime(line, '%m/%d/%y %H:%M:%S')
    elif cpu is None:
        m = cpu_rx.match(line)
        if not m:
            continue
        cpu = C.CpuStat(m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
    elif len(io.keys()) == 5:
        stats.append(Stat(ts, cpu, io));
        ts = None
        cpu = None
        io = {}
    else:
        m = io_rx.match(line)
        if m:
            io[m.group(1)] = C.IoStat(m.group(2), m.group(3), m.group(4), m.group(5), m.group(6), m.group(7), m.group(8), m.group(9), m.group(10), m.group(11), m.group(12), m.group(13), m.group(14))

def write_rrd(cmd, stat_tuple, rrd_fname, ts):
    if rrd_fname not in cmd:
        template = ':'.join(stat_tuple._fields)
        cmd[rrd_fname] = ['rrdtool', 'update', os.path.join('/tmp/rrd', rrd_fname), '--template', template, '--']
    values = ':'.join(str(v) for v in stat_tuple)
    cmd[rrd_fname].append(str(int(time.mktime(ts.timetuple()))) + ':' + values)

cmd = {}
for stat in stats:
    write_rrd(cmd, stat.cpu, 'cpu.rrd', stat.ts)
    for drive, io in stat.io.iteritems():
        write_rrd(cmd, io, 'hdd_' + drive + '.rrd', stat.ts)

for c in cmd.values():
    print(len(c))
    assert Popen(c).wait() == 0