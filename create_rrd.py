#!/usr/bin/python

import rrd_config as C
import os
import subprocess
from smart_attributes import names as smart_names

if not os.path.isdir(C.rrd_path):
    os.makedirs(C.rrd_path)

def mk_rrd(struct, fname, ds='GAUGE', *args):
    cmd = ['rrdtool', 'create', os.path.join(C.rrd_path, fname), '--step', '60', '--no-overwrite'] + list(args) +\
        ['DS:{}:{}:300:0:U'.format(field, ds) for field in struct._fields] +\
        ['RRA:AVERAGE:0.5:1:60',
         'RRA:AVERAGE:0.5:1:400',
         'RRA:AVERAGE:0.5:4:360',
         'RRA:AVERAGE:0.5:25:403',
         'RRA:AVERAGE:0.5:108:400',
         'RRA:AVERAGE:0.5:1314:800']
    #print(cmd)
    subprocess.Popen(cmd).wait()

def mk_smart_rrd(drive):
    cmd = ['rrdtool', 'create', os.path.join(C.rrd_path, 'smart_' + drive + ".rrd"), '--step', '60', '--no-overwrite'] +\
        ['DS:{}:GAUGE:300:0:U'.format(field_name) for field_name in C.attr_field_name_gtor(smart_names.keys())] +\
        ['RRA:AVERAGE:0.5:1:60',
         'RRA:AVERAGE:0.5:1:400',
         'RRA:AVERAGE:0.5:4:360',
         'RRA:AVERAGE:0.5:25:403',
         'RRA:AVERAGE:0.5:108:400',
         'RRA:AVERAGE:0.5:1314:800']
    #print(cmd)
    subprocess.Popen(cmd).wait()

mk_rrd(C.CpuStat, 'cpu.rrd')
map(lambda drive: mk_rrd(C.IoStat, 'hdd_{}.rrd'.format(drive)), C.drives)
map(mk_smart_rrd, C.drives)
mk_rrd(C.CpuLa, 'cpu_la.rrd')
map(lambda dev: mk_rrd(C.Traffic, 'traffic_{dev}.rrd'.format(dev=dev), 'COUNTER'), C.network_devices)
mk_rrd(C.Sockets, 'sockets.rrd')
mk_rrd(C.Ups, 'ups.rrd')
