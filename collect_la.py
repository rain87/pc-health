#!/usr/bin/python

import rrd_config as C
import re
from subprocess import Popen
import os
import sys

rx = re.compile('(\d+\.\d+) (\d+\.\d+) (\d+\.\d+)')
with open('/proc/loadavg', 'rt') as f:
    m = rx.match(f.readline())
    if not m:
        sys.exit(1)
    la = C.CpuLa(m.group(1), m.group(2), m.group(3))
    assert Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'cpu_la.rrd'),
        '--template', ':'.join(la._fields), '--',
        'N:' + ':'.join(la)]).wait() == 0
