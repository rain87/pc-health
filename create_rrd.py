#!/usr/bin/python

import rrd_config as C
import os
import subprocess

if not os.path.isdir(C.rrd_path):
    os.makedirs(C.rrd_path)

def mk_rrd(struct, fname, *args):
    cmd = ['rrdtool', 'create', os.path.join(C.rrd_path, fname), '--step', '60'] + list(args) +\
        ['DS:{}:GAUGE:300:0:U'.format(field) for field in struct._fields] +\
        ['RRA:LAST:0.5:1:60',
         'RRA:LAST:0.5:1:400',
         'RRA:AVERAGE:0.5:4:360',
         'RRA:AVERAGE:0.5:25:403',
         'RRA:AVERAGE:0.5:108:400',
         'RRA:AVERAGE:0.5:1314:800']
#    print(cmd)
    assert subprocess.Popen(cmd).wait() == 0

#mk_rrd(C.CpuStat, 'cpu.rrd')
#for drive in ['a', 'b', 'c', 'd', 'e', 'f']:
#    mk_rrd(C.IoStat, 'hdd_sd{}.rrd'.format(drive))
#mk_rrd(C.CpuLa, 'cpu_la.rrd')
#mk_rrd(C.Traffic, 'traffic.rrd')
#mk_rrd(C.Sockets, 'sockets.rrd')
mk_rrd(C.Ups, 'ups.rrd')
