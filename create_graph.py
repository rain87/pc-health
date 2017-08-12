#!/usr/bin/python

import rrd_config as C
import os
import subprocess
from collections import namedtuple
import gzip

DataSource = namedtuple('DataSource', 'db_fname field legend')
Graph = namedtuple('Graph', 'fname title vlabel ds area')

def hdd_ds(field):
    return [ DataSource('hdd_sd' + d + '.rrd', field, 'sd' + d) for d in 'abcdef' ]

def traffic_ds(units, direction):
    return [ DataSource('traffic.rrd', '{proto}_{units}_{direction}'.format(proto=proto, units=units, direction=direction), proto.upper())
        for proto in ['tcp', 'udp', 'other']]

graph_colors = [ '#396AB1', '#DA7C30', '#3E9651', '#CC2529', '#535154', '#6B4C9A', '#922428', '#948B3D' ]
graphs = [
    Graph('hdd_rrqm_s', 'Read requests merged per second that were queued to the device', 'rrqm/s', hdd_ds('rrqm_s'), False),
    Graph('hdd_wrqm_s', 'Write requests merged per second that were queued to the device', 'wrqm/s ', hdd_ds('wrqm_s'), False),
    Graph('hdd_r_s', 'Read requests that were issued to the device per second', 'r/s', hdd_ds('r_s'), False),
    Graph('hdd_w_s', 'Write requests that were issued to the device per second', 'w/s', hdd_ds('w_s'), False),
    Graph('hdd_rkB_s', 'Kilobytes read from the device per second', 'rkB/s ', hdd_ds('rkB_s'), False),
    Graph('hdd_wkB_s', 'Kilobytes written to the device per second', 'wkB/s ', hdd_ds('wkB_s'), False),
    Graph('hdd_avgrq_sz', 'Avg size of the requests that were issued to the device', 'sectors', hdd_ds('avgrq_sz'), False),
    Graph('hdd_avgqu_sz', 'Avg queue length of the requests that were issued to the device', 'requests', hdd_ds('avgqu_sz'), False),
    Graph('hdd_await', 'Avg time for I/O requests issued to the device to be served', 'milliseconds', hdd_ds('await'), False),
    Graph('hdd_r_await', 'Avg time for READ requests issued to the device to be served', 'milliseconds', hdd_ds('r_await'), False),
    Graph('hdd_w_await', 'Avg time for WRITE requests issued to the device to be served', 'milliseconds', hdd_ds('w_await'), False),
    Graph('hdd_svctm', '(OBSOLETE) Avg service time for I/O requests that were issued to the device', 'milliseconds', hdd_ds('svctm'), False),
    Graph('hdd_util', 'Percentage of CPU time during which I/O requests were issued to the device', '%', hdd_ds('util'), False),
    Graph('cpu_load', 'CPU loads', '%', [ DataSource('cpu.rrd', field, field) for field in C.CpuStat._fields if field != 'idle'], True),
    Graph('cpu_la', 'CPU load averages', None, [ DataSource('cpu_la.rrd', field, field) for field in C.CpuLa._fields], False),
    Graph('traffic_in_bytes', 'Incoming traffic', 'bytes', traffic_ds('bytes', 'in'), True),
    Graph('traffic_out_bytes', 'Outgoing traffic', 'bytes', traffic_ds('bytes', 'out'), True),
    Graph('traffic_in_pckts', 'Incoming traffic', 'packets', traffic_ds('pckts', 'in'), True),
    Graph('traffic_out_pckts', 'Outgoing traffic', 'packets', traffic_ds('pckts', 'out'), True),
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
        cmd.append('DEF:v{i}={db}:{field}:AVERAGE'.format(i=i, db=os.path.join(C.rrd_path, ds_list[i].db_fname), field=ds_list[i].field))
        cmd.append('{type}:v{i}{color}:{legend}{stack}'.format(type='AREA' if graph.area else 'LINE1',
            i=i, color=graph_colors[i], legend=ds_list[i].legend, stack=':STACK' if graph.area else ''))
    #print(' '.join(cmd))
    rrd = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    gz = gzip.open(os.path.join(C.graph_path, graph.fname + '_' + interval + '.svgz'), 'wb')
    while rrd.poll() is None:
        gz.write(rrd.stdout.read())
    gz.close()
    assert rrd.poll() == 0

for graph in graphs:
    #for interval in graph_intervals.keys():
    plot(graph, 'optimal')
#plot(graphs[-1], 'optimal')
