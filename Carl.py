#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2007  Tobias Klausmann
#
"""
An rsync logfile analyzer.

Intended to be used mainly by Gentoo Rsync Mirror admins
"""
import sys
import time
import md5

from optparse import OptionParser

import Accounts
import Sessions

__revision__ = "0.6"

# This script was originally intended for Gentoo rsync
# mirrors only. If you want, you can tune the rsync module
# name here. No trailing slashes, no regex or other fancy
# stuff.
__MODULE__ = "gentoo-portage"

# I pity the guy who has to add "E" (Exa) to the end of this list
__SIPREFIXES__ = ["", "k", "M", "G", "T", "P"]

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
       If logfile is not specified, it's read from stdin.""" % sys.argv[0]

def crunch(number, div=1024):
    """
    Repeatedly divides a number by div until it is smaller than div 
    """
    # Make sure it's a float
    div *= 1.0
    passes = 0
    while number > div:
        number /= div
        passes += 1
    return (number, passes)


def ob(s, style):
    """
    Return an obfuscated version of the string if the
    global var style is set to True.
    """
    if style == "fancy":
        return md5.new(s).hexdigest()
    elif style == "simple":
        s=s[:s.rfind(".")]
        s=s[:s.rfind(".")]
        return "%s.x.x" %(s)
    else:
        return s

def main():
    """
    Main program.
    """
    usage = "usage: %prog [options] [filename]\n\nIf filename is not specified, read from stdin"
    parser = OptionParser(usage=usage, version="%%prog %s" % __revision__)
    parser.add_option("-o", "--obfuscation", action="store", type="string",
                    dest="ostyle", default="none",
                    help="obfuscation style (simple, fancy, none) [%default]")
    parser.add_option("-r", "--reverse", action="store_true", 
                   dest="reverse", help="set reverse (classic) display order")
    (options, args) = parser.parse_args()

    print "Carl (Carl Analyzes Rsync Logfiles) %s" % __revision__
    print "(C) Tobias Klausmann"
    if __psyco_enabled__:
        print "Psyco found and enabled."

    if len(args) > 0:
        fname = args[0]
        try:
            logfd = open(fname, "r")
        except IOError, eobj:
            print "Cannot open '%s' for reading: %s" % (fname, eobj.strerror)
            sys.exit(1)
        print "Reading from '%s'" %(fname)

    else:
        logfd = sys.stdin
        print "Reading from stdin"

    ipc = Accounts.Accounts()
    ipb = Accounts.Accounts()
    sessions = Sessions.Sessions()
    ip2hname = {}

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
            if msg.startswith("rsync on %s" % (__MODULE__) ) and \
                not msg.startswith("rsync on %s/metadata" % (__MODULE__)) and \
                not msg.startswith("rsync on %s//metadata" % (__MODULE__)):
                try:
                    hname, ipaddr = msg.split(" ", 6)[4:6]
                except ValueError:
                    continue
                ipaddr = ipaddr[1:-2] # remove ()
                # Do some hostname caching which can be used for 
                # output later
                if hname!="UNKNOWN" and not ip2hname.get(ipaddr):
                    ip2hname[ipaddr] = hname
                ipc.incr(ipaddr)
                sessions.push(pid, '%s' % (ipaddr))

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

        # Now, generate the report.
        #
        tt, pfxn = crunch(totaltraffic)
        print "Total traffic: %.2f %sBytes" % (tt, __SIPREFIXES__[pfxn])
        print "Total number of sessions:", sessions.seencount
        print "Total number of unique IPs:", ipb.seencount
        print "Log seems to span %0.2f days." % (span)
        print
        print " Top 10 Hosts by byte count"
        print "Rank bytes     ( Bytes )     IP-Address"
        print "-----------------------------------------"
        top10list = ipb.counts()[-10:]
        ranklist = range(1,11)
        if not options.reverse:
            top10list.reverse()
            ranklist.reverse()
        for entry in top10list:
            sbytes, pfxn = crunch(entry[0])
            print "%2s %12s (%9.2f%s) %15s %s" % \
                (ranklist.pop(), entry[0], sbytes, __SIPREFIXES__[pfxn], ob(entry[1], options.ostyle), ob(ip2hname.get(entry[1], ""), options.ostyle))

        print "-----------------------------------------"
        savg, pfxn = crunch(totaltraffic/span)
        print "Average traffic per day: %0.2f bytes (%0.2f%sB)"% \
            (totaltraffic/span, savg, __SIPREFIXES__[pfxn])

        ttop5num = long(ipb.seencount*0.05)
        ttop5traffic = 0L
        for entry in ipb.counts()[-ttop5num:]:
            ttop5traffic += entry[0]
        
        stop, pfxn = crunch(ttop5traffic)
        print \
         "Top 5%% of IPs (%s) account for %s bytes (%0.2f%sB) of traffic," % \
         (ttop5num,ttop5traffic,stop,__SIPREFIXES__[pfxn])
        print "which is %0.2f%% of the total traffic."% \
         (ttop5traffic/(totaltraffic/100.0))

           
        print

        print " Top 10 Hosts by session count"
        print "Rank Sess.   per day    IP-Address"
        print "----------------------------------"
        top10list = ipc.counts()[-10:]
        ranklist = range(1,11)
        if not options.reverse:
            top10list.reverse()
            ranklist.reverse()
        for entry in top10list:
            print "%2s %6s    %6.2f   %15s %s"  % (ranklist.pop(), entry[0], entry[0]/span, ob(entry[1], options.ostyle), ob(ip2hname.get(entry[1], ""), options.ostyle))

        print "----------------------------------"
        print "Average number of sessions per day: %0.2f" % \
            (sessions.seencount/span)

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
    except ValueError:
        sys.stderr.write("Your logfile has a very strange format.\n")
        sys.exit(2)

if __name__ == "__main__":
    main()
