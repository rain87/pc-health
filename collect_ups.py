#!/usr/bin/python

import rrd_config as C
import re
import subprocess
import os

values = [None] * len(C.Ups._fields)
apc = subprocess.Popen(['apcaccess'], stdout=subprocess.PIPE)

while True:
    line = apc.stdout.readline()
    if not line:
        break
    for i in range(0, len(C.Ups._fields)):
        if line.startswith(C.Ups._fields[i]):
            m = re.search('.*:\s+(\d+(?:.\d+|))', line)
            if m:
                values[i] = m.group(1)

assert None not in values
assert subprocess.Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'ups.rrd'),
    '--template', ':'.join(C.Ups._fields), '--',
    'N:' + ':'.join(values)]).wait() == 0