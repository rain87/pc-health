#!/usr/bin/python
# coding=utf8

import rrd_config as C
import os
import subprocess
from collections import namedtuple
import gzip
import sys
import itertools
from smart_attributes import names as smart_names


DataSource = namedtuple('DataSource', 'db_fname field legend is_area color stack')
DataSource.__new__.__defaults__ = (False, None, False)
Graph = namedtuple('Graph', 'fname title vlabel ds')
graph_colors = [ '#396AB1', '#DA7C30', '#3E9651', '#CC2529', '#535154', '#6B4C9A', '#922428', '#948B3D', '#00adb5', '#f08a5d' ]

def hdd_ds(field):
    return [ DataSource('hdd_' + d + '.rrd', field, d, False) for d in C.drives ]

def traffic_ds(units, direction):
    color = itertools.cycle(graph_colors[:3])
    field = '_{units}_{direction}'.format(units=units, direction=direction)
    return [
        DataSource(db_fname='traffic_{dev}.rrd'.format(dev=dev), field=proto + field,
            legend='{}-{}'.format(dev, proto.upper()), is_area=True, color=color.next())
        for dev, proto in itertools.product(C.network_devices[:-1], ['tcp', 'udp', 'all'])
    ] + [
         DataSource('traffic_eth0.rrd', 'tcp' + field, '', False, ''),
         DataSource('traffic_eth0.rrd', 'udp' + field, '', False, '', True),
         DataSource('traffic_eth0.rrd', 'all' + field, 'eth0', False, '#000000', True)
    ]

def connections_ds(direction):
    color = itertools.cycle(graph_colors[:2])
    return [
        DataSource(db_fname='traffic_{dev}.rrd'.format(dev=dev),
            field='{proto}_new_{direction}'.format(proto=proto, direction=direction),
            legend='{}-{}'.format(dev, proto),
            is_area=True, color=color.next())
        for dev, proto in itertools.product(C.network_devices, ['tcp', 'udp'])
    ]

def smart_graph(attr, field, label=None):
    sattr = str(attr).zfill(3)
    return Graph('smart_' + sattr, '{} ({}-{})'.format(smart_names[attr], sattr, field), label,
        [ DataSource('smart_' + hdd + '.rrd', 'a{}_{}'.format(sattr, field), hdd, False) for hdd in C.drives ])

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
    Graph('traffic_in_bytes', 'Incoming bytes', 'bytes/s', traffic_ds('bytes', 'in')),
    Graph('traffic_out_bytes', 'Outgoing bytes', 'bytes/s', traffic_ds('bytes', 'out')),
    Graph('traffic_in_pckts', 'Incoming packets', 'packets/s', traffic_ds('pckts', 'in')),
    Graph('traffic_out_pckts', 'Outgoing packets', 'packets/s', traffic_ds('pckts', 'out')),
    Graph('incoming_connections', 'Incoming connections', 'count', connections_ds('in')),
    Graph('outgoing_connections', 'Outgoing connections', 'count', connections_ds('out')),
    Graph('sockets', 'Sockets', 'sockets',
        [ DataSource('sockets.rrd', field, field, True) for field in 'estab closed orphaned synrecv tw tw2'.split(' ') ] +\
        [ DataSource('sockets.rrd', field, field, False) for field in 'total tcp ports'.split(' ') ]),
    Graph('ups_v', 'Voltages', 'volts', [ DataSource('ups.rrd', 'LINEV', 'AC line', False), DataSource('ups.rrd', 'BATTV', 'UPS battery', False)]),
    Graph('ups_load', 'Load and charge', '%', [ DataSource('ups.rrd', 'LOADPCT', 'UPS load', False), DataSource('ups.rrd', 'BCHARGE', 'Battery charge', False) ]),
    Graph('ups_misc', 'Misc UPS stats', None, [ DataSource('ups.rrd', 'TIMELEFT', 'Time on battery left', False),
        DataSource('ups.rrd', 'NUMXFERS', 'Number of transfers', False), DataSource('ups.rrd', 'TONBATT', 'Time on battery', False),
        DataSource('ups.rrd', 'CUMONBATT', 'CUMONBATT', False) ]),
    smart_graph(194, 'raw', '°C'),
    smart_graph(1, 'cur'),
    smart_graph(3, 'raw', 'msec'),
    smart_graph(4, 'raw'),
    smart_graph(7, 'cur'),
    smart_graph(9, 'raw'),
    smart_graph(11, 'raw'),
    smart_graph(12, 'raw'),
    smart_graph(195, 'cur'),
]

graph_intervals = {
    'hourly': 'now-1h',
    'optimal': 'now-400m',
    'daily': 'now-1d',
    'weekly': 'now-1w',
    'monthly': 'now-30d',
    'yearly': 'now-1y'
}

def plot(graph, interval):
    assert interval in graph_intervals
    cmd = ['rrdtool', 'graph', '-' , '--start', graph_intervals[interval], '--title', graph.title, '--imgformat', 'SVG',
        '--lower-limit', '0' ]
    if graph.vlabel:
        cmd += ['--vertical-label', graph.vlabel]
    ds_list = graph.ds if isinstance(graph.ds, list) else [graph.ds]
    color = itertools.cycle(graph_colors)
    for i in range(0, len(ds_list)):
        ds = ds_list[i]
        cmd.append('DEF:v{i}={db}:{field}:AVERAGE'.format(i=i, db=os.path.join(C.rrd_path, ds.db_fname), field=ds.field))
        cmd.append('{type}:v{i}{color}:{legend}{stack}'.format(
            type='AREA' if ds.is_area else 'LINE1', i=i, color=color.next() if ds.color is None else ds.color,
            legend=ds.legend, stack=':STACK' if ds.is_area or ds.stack else ''))
    #print(' '.join(cmd))
    rrd = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    gz = gzip.open(os.path.join(C.graph_path, graph.fname + '_' + interval + '.svgz'), 'wb')
    while rrd.poll() is None:
        gz.write(rrd.stdout.read())
    gz.close()
    assert rrd.poll() == 0

for graph in graphs:
    plot(graph, sys.argv[1])
