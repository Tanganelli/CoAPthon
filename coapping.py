#!/usr/bin/env python2

# COAP ping implementation
# 0x4000 0001 <-->  0x7000 0001
# 0x4000 0002 <-->  0x7000 0002
# 0x4000 0003 <-->  0x7000 0003

import socket
import struct
import sys
from time import sleep, time
from optparse import OptionParser


# Parse Options
if __name__ == '__main__':
    parser = OptionParser()

    parser.add_option("-n", "--hostname",
        action="append",
        dest="host_name",
        help="Define COAP host name")

    parser.add_option("-p", "--port",
        action="append",
        dest="host_port",
        default=5683,
        help="Define COAP host port (default: 5683)")

    parser.add_option("-l", "--loops",
        type="int",
        dest="ping_loops",
        default=0,
        help="Number of ping loops (default: 0 - forever)")

    parser.add_option("-t", "--sleep",
        type="float",
        dest="sleep_sec",
        default=1,
        help="Time in seconds between two pings (default: 1 sec)")

    (options, args) = parser.parse_args()

    # COAP ping parameters setup
    host = options.host_name[0]
    port = options.host_port
    sleep_sec = options.sleep_sec
    ping_loops = options.ping_loops

    ping_no = 1     # ping payload counter
    ping_cnt = 0    # global ping cnt

    print 'COAP ping script'
    print 'COAP ping to: %s:%s...' % (host, port)

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except socket.error:
        print 'Error: Failed to create socket'
        sys.exit()

    while(1):
        loop_time = time()
        msg = ''    #[0x40, 0x00, 0x00, 0x00]

        msg += struct.pack("B", 0x40)
        msg += struct.pack("B", 0x00)
        msg += struct.pack("B", 0x00)
        msg += struct.pack("B", ping_no)

        try :
            print '[0x%08X] Send ping:' % (ping_cnt), [hex(ord(c)) for c in msg]
            #Set the whole string
            s.sendto(msg, (host, port))
            s.settimeout(2 + sleep_sec)

            # receive data from client (data, addr)
            d = s.recvfrom(4)
            reply = d[0]
            addr = d[1]

            # We need to check if ping peyload counter is the same in reply
            status = bytes(msg)[3] == bytes(reply)[3]
            print '[0x%08X] Recv ping:' % (ping_cnt), [hex(ord(c)) for c in reply], 'ok' if status else 'fail'

        except socket.error as e:
            print 'Error: socket.error: ', str(e)
            #print 'Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
            sleep(3)    # Waiting to recover ;)
        except socket.timeout:
            print("Error: closing socket")
            s.close()

        if ping_no >= 0xFF:
            ping_no = 1
        else:
            ping_no += 1

        sleep(sleep_sec - (time() - loop_time))
        print 'In %.2f sec' % (time() - loop_time)

        if ping_loops > 0:
            if ping_loops == 1:
                break
            ping_loops -= 1

        ping_cnt += 1
