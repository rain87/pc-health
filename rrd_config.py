from collections import namedtuple

rrd_path = '/var/lib/rrd'
graph_path = '/var/www/pc-health'

#rrd_path = '/tmp/test'
#graph_path = '/tmp/test'

IoStat = namedtuple('IoStat', 'rrqm_s wrqm_s r_s w_s rkB_s wkB_s avgrq_sz avgqu_sz await r_await w_await svctm util')
CpuStat = namedtuple('CpuStat', 'user nice system iowait steal idle')
CpuLa = namedtuple('CpuLa', 'la1 la5 la10')
Traffic = namedtuple('Traffic', 'tcp_bytes_in tcp_bytes_out udp_bytes_in udp_bytes_out all_bytes_in all_bytes_out'\
    ' tcp_pckts_in tcp_pckts_out udp_pckts_in udp_pckts_out all_pckts_in all_pckts_out'\
    ' tcp_new_in udp_new_in tcp_new_out udp_new_out')
Sockets = namedtuple('Sockets', 'total tcp estab closed orphaned synrecv tw tw2 ports')
Ups = namedtuple('Ups', 'LINEV LOADPCT BCHARGE TIMELEFT BATTV NUMXFERS TONBATT CUMONBATT')

network_devices = 'tun1 tun2 tun3 tun4 tun5 eth0'.split(' ')
