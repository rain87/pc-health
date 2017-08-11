#!/usr/bin/python

import rrd_config as C
import os
import subprocess
from collections import namedtuple

DataSource = namedtuple('DataSource', 'db_fname field legend')
Graph = namedtuple('Graph', 'fname title vlabel lowerlimit upperlimit ds')

def hdd_ds(field):
    return [ DataSource('hdd_sd' + d + '.rrd', field, 'sd' + d) for d in 'abcdef' ]

graph_colors = [ '#396AB1', '#DA7C30', '#3E9651', '#CC2529', '#535154', '#6B4C9A', '#922428', '#948B3D' ]
graphs = [
    Graph('hdd_rrqm_s', 'Read requests merged per second that were queued to the device', 'rrqm/s', 0, None, hdd_ds('rrqm_s')),
    Graph('hdd_wrqm_s', 'Write requests merged per second that were queued to the device', 'wrqm/s ', 0, None, hdd_ds('wrqm_s')),
    Graph('hdd_r_s', 'Read requests that were issued to the device per second', 'r/s', 0, None, hdd_ds('r_s')),
    Graph('hdd_w_s', 'Write requests that were issued to the device per second', 'w/s', 0, None, hdd_ds('w_s')),
    Graph('hdd_rkB_s', 'Kilobytes read from the device per second', 'rkB/s ', 0, None, hdd_ds('rkB_s')),
    Graph('hdd_wkB_s', 'Kilobytes written to the device per second', 'wkB/s ', 0, None, hdd_ds('wkB_s')),
    Graph('hdd_avgrq_sz', 'Avg size of the requests that were issued to the device', 'sectors', 0, None, hdd_ds('avgrq_sz')),
    Graph('hdd_avgqu_sz', 'Avg queue length of the requests that were issued to the device', 'requests', 0, None, hdd_ds('avgqu_sz')),
    Graph('hdd_await', 'Avg time for I/O requests issued to the device to be served', 'milliseconds', 0, None, hdd_ds('await')),
    Graph('hdd_r_await', 'Avg time for READ requests issued to the device to be served', 'milliseconds', 0, None, hdd_ds('r_await')),
    Graph('hdd_w_await', 'Avg time for WRITE requests issued to the device to be served', 'milliseconds', 0, None, hdd_ds('w_await')),
    Graph('hdd_svctm', '(OBSOLETE) Avg service time for I/O requests that were issued to the device', 'milliseconds', 0, None, hdd_ds('svctm')),
    Graph('hdd_util', 'Percentage of CPU time during which I/O requests were issued to the device', '%', 0, None, hdd_ds('util'))
#    Graph('cpu_load', 'CPU loads', '%', 0, None, [ DataSource('cpu.rrd', field, field) for field in CpuStat._fields]),
#    Graph('cpu_la', 'CPU load averages', None, 0, None, [ DataSource('cpu_la.rrd', field, field) for field in CpuLa._fields]),
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
    cmd = ['rrdtool', 'graph', os.path.join(C.graph_path, graph.fname + '_' + interval + '.svg'), '--start',
        graph_intervals[interval], '--title', graph.title, '--imgformat', 'SVG' ]
    if graph.vlabel:
        cmd += ['--vertical-label', graph.vlabel]
    if graph.lowerlimit:
        cmd += ['--lower-limit', graph.lowerlimit]
    if graph.upperlimit:
        cmd += ['--upper-limit', graph.upperlimit]
    ds_list = graph.ds if isinstance(graph.ds, list) else [graph.ds]
    num = 0
    for ds in ds_list:
        vname = (ds.db_fname + ds.field).replace('.', '_')
        cmd.append('DEF:{vname}={db}:{field}:AVERAGE'.format(vname=vname, db=os.path.join(C.rrd_path, ds.db_fname), field=ds.field))
        cmd.append('LINE1:{vname}{color}:"{legend}"'.format(num=num + 1, vname=vname, color=graph_colors[num], legend=ds.legend))
        num += 1
        assert num < len(graph_colors)
#    print(cmd)
    assert subprocess.Popen(cmd).wait() == 0

for graph in graphs:
    for interval in graph_intervals.keys():
        plot(graph, interval)
