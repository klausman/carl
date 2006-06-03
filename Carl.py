#!/usr/bin/python
"""
A very simplistic rsync logfile analyzer.

Intended to be used mainly by Gentoo Rsync Mirror admins
"""
import sys
import time

import Account
import Sessions

__revision__ = "0.3"

try:
    import psyco
    psyco.full()
    __psyco_enabled__ = True
except ImportError:
    __psyco_enabled__ = False

def usage():
    """
    Print out short usage info.
    """
    print """Usage: %s [logfile]
       Alternatively, logfile is read from stdin.""" % sys.argv[0]

def main():
    """
    Main program.
    """
    print "Carl (Carl Analyzes Rsync Logfiles) %s" % __revision__
    print "(C) Tobias Klausmann"
    if __psyco_enabled__:
        print "Psyco found and enabled."

    if len(sys.argv)>1 and sys.argv[1] in ["-h", "--help"]:
        usage()
        sys.exit(0)

    if len(sys.argv) > 1:
        fname = sys.argv[1]
        try:
            logfd = open(fname, "r")
        except IOError, eobj:
            print "Cannot open %s for reading: %s" % (fname, eobj.strerror)
            sys.exit(1)
        print "Reading from", fname

    else:
        logfd = sys.stdin
        print "Reading from stdin"

    ipc = Account.Account()
    ipb = Account.Account()
    sessions = Sessions.Sessions()

    linecount = 0
    totaltraffic = 0L

    sys.stdout.flush()

    rtime = time.time()
    line = ""
    try:
        for line in logfd:
            linecount += 1
            if linecount == 1:
                # timefmt: 2004/02/23 23:11:27 
                ldate, ltime = line.split(None, 2)[0:2]
                start = time.mktime(time.strptime("%s %s"%(ldate, ltime), \
                    "%Y/%m/%d %H:%M:%S"))
                

            pid, msg = line[20:].split(" ", 1)
            if msg.startswith("rsync on gentoo-") and \
                not msg.startswith("rsync on gentoo-portage/metadata") and \
                not msg.startswith("rsync on gentoo-portage//metadata"):
                try:
                    hname, ipaddr = msg.split(" ", 6)[4:6]
                except ValueError:
                    continue
                ipc.incr('%15s (%s)'%(ipaddr[1:-2], hname))
                sessions.push(pid, '%15s (%s)' % (ipaddr[1:-2], hname))

            elif msg.startswith("sent"):
                try:
                    values = msg.split(" ", 11)
                    wbytes = values[1]
                    rbytes = values[5]
                except ValueError:
                    continue
                ipaddr = sessions.pop(pid)
                ipb.incr(ipaddr, int(wbytes)+int(rbytes))
                totaltraffic += long(rbytes)+long(wbytes)

        ldate, ltime = line.split(None, 2)[0:2]
        span = (time.mktime(time.strptime("%s %s" % (ldate, ltime), \
            "%Y/%m/%d %H:%M:%S"))-start) / (24*3600)
        rtime = time.time()-rtime

        del (logfd)
        print "Total traffic: %0.2f GBytes" % (totaltraffic/(1024*1024*1024.0))
        print "Total number of unique IPs:", ipb.seencount
        print "Log seems to span %0.2f days." % (span)
        print
        print " Top 10 Hosts by bytes"
        print "     bytes ( MBytes )     IP-Adress   (Hostname)"
        print "------------------------------------------------"
        for entry in ipb.counts()[-10:]:
            print "%10s (%7.2fM) %s" % \
                (entry[0], entry[0]/(1024*1024.0), entry[1])

        print "------------------------------------------------"

        ttop5num = long(ipb.seencount*0.05)
        ttop5traffic = 0L
        for entry in ipb.counts()[-ttop5num:]:
            ttop5traffic += entry[0]

        print \
         "Top 5%% of IPs (%s) account for %s bytes (%0.2fGB) of traffic." % \
         (ttop5num,ttop5traffic,ttop5traffic/(1024*1024*1024.0))
        print "which is %0.2f%% of the total traffic."% \
         (ttop5traffic/(totaltraffic/100.0))

           
        print

        print " Top 10 Hosts by number of sessions"
        print "Sessions   per day    IP-Adress   (Hostname)"
        print "-------------------------------------"
        for entry in ipc.counts()[-10:]:
            print "%6s      %5.2f %s"  % (entry[0], entry[0]/span, entry[1])

        print "-------------------------------------"
        print "Total number of sessions..........:", sessions.seencount
        print "Average number of sessions per day: %0.2f" % \
            (sessions.seencount/span)
        print

        stop5num = long(ipc.seencount*0.05)
        stop5sessions = 0L
        for entry in ipc.counts()[-stop5num:]:
            stop5sessions += entry[0]
        print "Top 5%% of IPs (%s) account for %s sessions." % \
         (stop5num,stop5sessions)
        print "which is %0.2f%% of the total number of sessions." % \
         (stop5sessions/(sessions.seencount/100.0))
        print 

        print "Analyzed %s lines in %0.2f seconds, %0.2f lines per second" % \
         (linecount,rtime,linecount/rtime)
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted. Probably your fault.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
