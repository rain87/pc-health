#!/usr/bin/python

import rrd_config as C
import os
import subprocess
from collections import namedtuple
import gzip
import sys

DataSource = namedtuple('DataSource', 'db_fname field legend is_area')
Graph = namedtuple('Graph', 'fname title vlabel ds')

def hdd_ds(field):
    return [ DataSource('hdd_sd' + d + '.rrd', field, 'sd' + d, False) for d in 'abcdef' ]

def traffic_ds(units, direction):
    return [ DataSource('traffic.rrd', '{proto}_{units}_{direction}'.format(proto=proto, units=units, direction=direction), proto.upper(), True)
        for proto in ['tcp', 'udp', 'other']]

graph_colors = [ '#396AB1', '#DA7C30', '#3E9651', '#CC2529', '#535154', '#6B4C9A', '#922428', '#948B3D', '#00adb5', '#f08a5d' ]
graphs = [
    Graph('hdd_rrqm_s', 'Read requests merged per second that were queued to the device', 'rrqm/s', hdd_ds('rrqm_s')),
    Graph('hdd_wrqm_s', 'Write requests merged per second that were queued to the device', 'wrqm/s ', hdd_ds('wrqm_s')),
    Graph('hdd_r_s', 'Read requests that were issued to the device per second', 'r/s', hdd_ds('r_s')),
    Graph('hdd_w_s', 'Write requests that were issued to the device per second', 'w/s', hdd_ds('w_s')),
    Graph('hdd_rkB_s', 'Kilobytes read from the device per second', 'rkB/s ', hdd_ds('rkB_s')),
    Graph('hdd_wkB_s', 'Kilobytes written to the device per second', 'wkB/s ', hdd_ds('wkB_s')),
    Graph('hdd_avgrq_sz', 'Avg size of the requests that were issued to the device', 'sectors', hdd_ds('avgrq_sz')),
    Graph('hdd_avgqu_sz', 'Avg queue length of the requests that were issued to the device', 'requests', hdd_ds('avgqu_sz')),
    Graph('hdd_await', 'Avg time for I/O requests issued to the device to be served', 'milliseconds', hdd_ds('await')),
    Graph('hdd_r_await', 'Avg time for READ requests issued to the device to be served', 'milliseconds', hdd_ds('r_await')),
    Graph('hdd_w_await', 'Avg time for WRITE requests issued to the device to be served', 'milliseconds', hdd_ds('w_await')),
    Graph('hdd_svctm', '(OBSOLETE) Avg service time for I/O requests that were issued to the device', 'milliseconds', hdd_ds('svctm')),
    Graph('hdd_util', 'Percentage of CPU time during which I/O requests were issued to the device', '%', hdd_ds('util')),
    Graph('cpu_load', 'CPU loads', '%', [ DataSource('cpu.rrd', field, field, True) for field in C.CpuStat._fields if field != 'idle']),
    Graph('cpu_la', 'CPU load averages', None, [ DataSource('cpu_la.rrd', field, field, False) for field in C.CpuLa._fields]),
    Graph('traffic_in_bytes', 'Incoming traffic', 'bytes', traffic_ds('bytes', 'in')),
    Graph('traffic_out_bytes', 'Outgoing traffic', 'bytes', traffic_ds('bytes', 'out')),
    Graph('traffic_in_pckts', 'Incoming traffic', 'packets', traffic_ds('pckts', 'in')),
    Graph('traffic_out_pckts', 'Outgoing traffic', 'packets', traffic_ds('pckts', 'out')),
    Graph('sockets', 'Sockets', 'sockets',
        [ DataSource('sockets.rrd', field, field, True) for field in 'estab closed orphaned synrecv tw tw2'.split(' ') ] +\
        [ DataSource('sockets.rrd', field, field, False) for field in 'total tcp ports'.split(' ') ]),
    Graph('ups_v', 'Voltages', 'volts', [ DataSource('ups.rrd', 'LINEV', 'AC line', False), DataSource('ups.rrd', 'BATTV', 'UPS battery', False)]),
    Graph('ups_load', 'Load and charge', '%', [ DataSource('ups.rrd', 'LOADPCT', 'UPS load', False) ]),
    Graph('ups_misc', 'Misc UPS stats', None, [ DataSource('ups.rrd', 'TIMELEFT', 'Time on battery left', False),
        DataSource('ups.rrd', 'NUMXFERS', 'Number of transfers', False), DataSource('ups.rrd', 'TONBATT', 'Time on battery', False),
        DataSource('ups.rrd', 'CUMONBATT', 'CUMONBATT', False) ]),
]

graph_intervals = {
    'hourly': 'now-1h',
    'optimal': 'now-400m',
    'daily': 'now-1d',
    'weekly': 'now-1w',
    'monthly': 'now-1m',
    'yearly': 'now-1y'
}

def plot(graph, interval):
    assert interval in graph_intervals
    cmd = ['rrdtool', 'graph', '-' , '--start', graph_intervals[interval], '--title', graph.title, '--imgformat', 'SVG',
        '--lower-limit', '0' ]
    if graph.vlabel:
        cmd += ['--vertical-label', graph.vlabel]
    ds_list = graph.ds if isinstance(graph.ds, list) else [graph.ds]
    assert len(ds_list) < len(graph_colors)
    for i in range(0, len(ds_list)):
        ds = ds_list[i]
        cmd.append('DEF:v{i}={db}:{field}:AVERAGE'.format(i=i, db=os.path.join(C.rrd_path, ds.db_fname), field=ds.field))
        cmd.append('{type}:v{i}{color}:{legend}{stack}'.format(type='AREA' if ds.is_area else 'LINE1',
            i=i, color=graph_colors[i], legend=ds.legend, stack=':STACK' if ds.is_area else ''))
    #print(' '.join(cmd))
    rrd = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    gz = gzip.open(os.path.join(C.graph_path, graph.fname + '_' + interval + '.svgz'), 'wb')
    while rrd.poll() is None:
        gz.write(rrd.stdout.read())
    gz.close()
    assert rrd.poll() == 0

for graph in graphs:
    plot(graph, sys.argv[1])
