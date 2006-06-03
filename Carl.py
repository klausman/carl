#!/usr/bin/python

import sys
import re
import time

import Account
import IPSessions
try:
    import psyco
except ImportError:
    pass

def usage():
    print """\
Usage: %s [logfile]
       Alternatively, logfile is read from stdin.
""" % sys.argv[0]


print "Carl (Carl Analyzes Rsync Logfiles) V0.2"
print "(C) Tobias Klausmann"

if len(sys.argv)>1 and sys.argv[1] in ["-h", "--help"]:
    usage()
    sys.exit(0)

if len(sys.argv) > 1:
    fn = sys.argv[1]
    try:
        fd=open(fn, "r")
    except Exception, e:
        print "Cannot open %s for reading: %s" % (fn,e.strerror)
        sys.exit(1)
    print "Reading from", fn

else:
    fd = sys.stdin
    print "Reading from stdin"

ipc=Account.Account()
ipb=Account.Account()
sessions=IPSessions.IPSessions()

linecount=0
totaltraffic=0L

sys.stdout.flush()

rtime=time.time()
try:
    for ll in fd:
        linecount+=1
        if linecount==1:
            # timefmt: 2004/02/23 23:11:27 
            d,t,i,r = ll.split(None, 3)
            start = time.mktime(time.strptime("%s %s"%(d,t), \
                "%Y/%m/%d %H:%M:%S"))
            

        pid,l=ll[20:].split(" ",1)
        if l.startswith("rsync on gentoo-") and not l.startswith("rsync on gentoo-portage/metadata") and not l.startswith("rsync on gentoo-portage//metadata"):
            try:
                r,o,m,f,hn,ip=l.split(" ",6)
            except:
                continue
            ipc.incr('%15s (%s)'%(ip[1:-2], hn))
            sessions.push(pid,'%15s (%s)'%(ip[1:-2], hn))

        elif l.startswith("sent"):
            try:
                w,wbytes,b,E,r,rbytes,b,E,t,s,tbytes=l.split(" ",11)
            except:
                continue
            ip=sessions.pop(pid)
            ipb.incr(ip,int(wbytes)+int(rbytes))
            totaltraffic+=long(rbytes)+long(wbytes)

    d,t,r = ll.split(None, 2)
    span = (time.mktime(time.strptime("%s %s"%(d,t), \
        "%Y/%m/%d %H:%M:%S"))-start) / (24*3600)
    rtime=time.time()-rtime

    del (fd)
    print "Total traffic: %0.2f GBytes"%(totaltraffic/(1024*1024*1024.0))
    print "Total number of unique IPs:",ipb.seencount
    print "Log seems to span %0.2f days." %(span)
    print
    print " Top 10 Hosts by bytes"
    print "     bytes ( MBytes )     IP-Adress   (Hostname)"
    print "------------------------------------------------"
    for e in ipb.counts()[-10:]:
        print "%10s (%7.2fM) %s"%(e[0], e[0]/(1024*1024.0), e[1])

    print "------------------------------------------------"

    ttop5num=long(ipb.seencount*0.05)
    ttop5traffic=0L
    for e in ipb.counts()[-ttop5num:]:
        ttop5traffic+=e[0]

#print "Top 5%% of IPs by traffic: %s\nThey account for %s bytes (%0.2fGB) of traffic."%\
#(ttop5num,ttop5traffic,ttop5traffic/(1024*1024*1024.0))
    print "Top 5%% of IPs (%s) account for %s bytes (%0.2fGB) of traffic."%\
    (ttop5num,ttop5traffic,ttop5traffic/(1024*1024*1024.0))
    print "which is %0.2f%% of the total traffic."%\
    (ttop5traffic/(totaltraffic/100.0))

       
    print

    print " Top 10 Hosts by number of sessions"
    print "Sessions   per day    IP-Adress   (Hostname)"
    print "-------------------------------------"
    for e in ipc.counts()[-10:]:
        print "%6s      %5.2f %s" %(e[0], e[0]/span, e[1])

    print "-------------------------------------"
    print "Total number of sessions..........:",sessions.seencount
    print "Average number of sessions per day: %0.2f"%(sessions.seencount/span)
    print

    stop5num=long(ipc.seencount*0.05)
    stop5sessions=0L
    for e in ipc.counts()[-stop5num:]:
        stop5sessions+=e[0]
    print "Top 5%% of IPs (%s) account for %s sessions."%\
    (stop5num,stop5sessions)
    print "which is %0.2f%% of the total number of sessions."%\
    (stop5sessions/(sessions.seencount/100.0))
    print 

    print "Analyzed %s lines in %0.2f seconds, %0.2f lines per second"%(linecount,rtime,linecount/rtime)
except KeyboardInterrupt:
    sys.stderr.write("Interrupted. Probably your fault.\n")
    sys.exit(1)

        
        
