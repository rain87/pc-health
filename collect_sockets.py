#!/usr/bin/python

import rrd_config as C
import re
import subprocess
import os

total_rx = re.compile('Total:\s+(\d+)')
tcp_rx = re.compile('TCP:\s+(\d+)\s+\(estab (\d+), closed (\d+), orphaned (\d+), synrecv (\d+), timewait (\d+)/(\d+)\), ports (\d+)')

ss = subprocess.Popen(['ss', '-s'], stdout=subprocess.PIPE)
m1 = total_rx.match(ss.stdout.readline())
m2 = tcp_rx.match(ss.stdout.readline())

assert m1 and m2
sock = C.Sockets(m1.group(1), *[m2.group(i) for i in range(1, 9)])

assert subprocess.Popen(['rrdtool', 'update', os.path.join(C.rrd_path, 'sockets.rrd'),
    '--template', ':'.join(sock._fields), '--',
    'N:' + ':'.join(sock)]).wait() == 0
