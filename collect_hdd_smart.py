#!/usr/bin/python

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import rrd_config as C
from pySMART import DeviceList
import datetime
import os
from smart_attributes import names as smart_names
from subprocess import Popen

def convert_attributes(smart):
    return C.SmartAttribute(int(smart.value), int(smart.worst), int(smart.thresh), int(smart.raw))

smart = { device.name: { i: convert_attributes(device.attributes[i])
                              for i in range(0, 256) if device.attributes[i] and i in smart_names }
              for device in DeviceList().devices }

for hdd, attributes in smart.iteritems():
    cmd = ['rrdtool', 'update', os.path.join(C.rrd_path, 'smart_' + hdd + '.rrd'), '--template'] +\
        [':'.join(C.attr_field_name_gtor(attributes.keys())), '--'] +\
        ['N:' + ':'.join(str(attributes[k][i]) for k in attributes.keys() for i in range(0, len(C.SmartAttribute._fields)))]
    assert Popen(cmd).wait() == 0

with open(os.path.join(C.graph_path, 'smart.html'), 'w') as f:
    f.write('<html><body><table border=1>')
    devices = sorted(smart.keys())
    f.write('<tr><td>Attribute name; value / worst / threshold (raw)</td>' + ''.join('<td>' + dev + '</td>' for dev in devices) + '</tr>')
    for i in range(1, 255):
        values = [smart[dev][i] if i in smart[dev] else None for dev in devices]
        if ''.join('1' if isinstance(v, C.SmartAttribute) else '' for v in values) != '':
            f.write('<tr><td>{}: {}</td>'.format(i, smart_names[i]) +
                ''.join('<td>{} / {} / {} ({})</td>'.format(v.cur, v.wst, v.thr, v.raw) if isinstance(v, C.SmartAttribute) else '<td>-</td>' for v in values) + '</tr>')
    f.write('</table></body></html>')

