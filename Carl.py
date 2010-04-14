#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2009  Tobias Klausmann
#
"""
An rsync logfile analyzer.

Intended to be used mainly by Gentoo Rsync Mirror admins
"""
import sys
import time
import hashlib

from optparse import OptionParser
from random import random

import Accounts
import Sessions

__revision__ = "0.9"

# This script was originally intended for Gentoo rsync
# mirrors only. If you want, you can tune the rsync module
# name here. No trailing slashes, no regex or other fancy
# stuff.
__MODULE__ = "gentoo-portage"

# I pity the guy who has to add "E" (Exa) to the end of this list
__SIPREFIXES__ = ["", "k", "M", "G", "T", "P"]

# This value is inserted into the IP adresses if they're obfuscated
# with MD5. This way, the same sum in the two top-ten lists means it's
# the same IP, yet it makes the use of even a partial rainbow table 
# unfeasible
SALT="%s" % (random())

try:
    import psyco
    psyco.full()
    __psyco_enabled__ = True
except ImportError:
    __psyco_enabled__ = False

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
    Return an obfuscated version of the string in the style specified
    (one of fancy, simple or everything else (being no obfuscation)).
    """
    if s!="" and style == "fancy":
        m = hashlib.md5()
        s+=SALT
        m.update(s.encode("utf8"))
        dig=m.hexdigest()
        return ("%s...%s" % (dig[:8], dig[-8:]))
    elif s!="" and style == "simple":
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
    lic="Licensed under the GPL v2 (see COPYING). No warranty whatsoever."
    parser = OptionParser(usage=usage, version="%%prog %s\n%s" \
        % (__revision__, lic))
    parser.add_option("-o", "--obfuscation", action="store", type="string",
                    dest="ostyle", default="none",
                    help="obfuscation style (simple, fancy, none) [%default]")
    parser.add_option("-r", "--reverse", action="store_true", 
                   dest="reverse", help="set reverse (classic) display order")
    parser.add_option("-s", "--short", action="store_true", 
                   dest="shortoutput", help="display only the two top-10 lists")
    (options, args) = parser.parse_args()

    if not options.shortoutput:
        print("Carl (Carl Analyzes Rsync Logfiles) %s" % __revision__)
        print("(C) Tobias Klausmann")
        if __psyco_enabled__:
            print("Psyco found and enabled.")

    if len(args) > 0:
        fname = args[0]
        try:
            logfd = open(fname, "r")
        except IOError as eobj:
            sys.stderr.write("Cannot open '%s' for reading: %s" % (fname, eobj.strerror))
            sys.exit(1)
        if not options.shortoutput:
            print("Reading from '%s'" %(fname))

    else:
        logfd = sys.stdin
        if not options.shortoutput:
            print("Reading from stdin")

    ipc = Accounts.Accounts()
    ipb = Accounts.Accounts()
    sessions = Sessions.Sessions()
    ip2hname = {}

    linecount = 0
    totaltraffic = 0

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
                totaltraffic += int(rbytes)+int(wbytes)

        ldate, ltime = line.split(None, 2)[0:2]
        span = (time.mktime(time.strptime("%s %s" % (ldate, ltime), \
            "%Y/%m/%d %H:%M:%S"))-start) / (24*3600)
        rtime = time.time()-rtime

        del (logfd)

        # Now, generate the report.
        #
        if not options.shortoutput:
            tt, pfxn = crunch(totaltraffic)
            print("Total traffic: %.2f %sBytes" % (tt, __SIPREFIXES__[pfxn]))
            print("Total number of sessions:", sessions.seencount)
            print("Total number of unique IPs:", ipb.seencount)
            print("Log seems to span %0.2f days." % (span))
            print()
        print(" Top 10 Hosts by byte count")
        print("Rank bytes     ( Bytes )     IP-Address")
        print("-----------------------------------------")
        top10list = ipb.counts()[-10:]
        ranklist = list(range(1,11))
        if not options.reverse:
            top10list.reverse()
            ranklist.reverse()
        for entry in top10list:
            sbytes, pfxn = crunch(entry[0])
            print("%2s %12s (%9.2f%s) %15s %s" % \
                (ranklist.pop(), entry[0], sbytes, __SIPREFIXES__[pfxn], ob(entry[1], options.ostyle), ob(ip2hname.get(entry[1], ""), options.ostyle)))

        print("-----------------------------------------")
        if not options.shortoutput:
            savg, pfxn = crunch(totaltraffic/span)
            print("Average traffic per day: %0.2f bytes (%0.2f%sB)"% \
                (totaltraffic/span, savg, __SIPREFIXES__[pfxn]))

            ttop5num = int(ipb.seencount*0.05)
            ttop5traffic = 0
            for entry in ipb.counts()[-ttop5num:]:
                ttop5traffic += entry[0]
            
            stop, pfxn = crunch(ttop5traffic)
            print("Top 5%% of IPs (%s) account for %s bytes (%0.2f%sB) of traffic," % \
             (ttop5num,ttop5traffic,stop,__SIPREFIXES__[pfxn]))
            print("which is %0.2f%% of the total traffic."% \
             (ttop5traffic/(totaltraffic/100.0)))

           
        print()

        print(" Top 10 Hosts by session count")
        print("Rank Sess.   per day    IP-Address")
        print("----------------------------------")
        top10list = ipc.counts()[-10:]
        ranklist = list(range(1,11))
        if not options.reverse:
            top10list.reverse()
            ranklist.reverse()
        for entry in top10list:
            print("%2s %6s    %6.2f   %15s %s"  % (ranklist.pop(), entry[0], entry[0]/span, ob(entry[1], options.ostyle), ob(ip2hname.get(entry[1], ""), options.ostyle)))

        print("----------------------------------")
        if not options.shortoutput:
            print("Average number of sessions per day: %0.2f" % \
                (sessions.seencount/span))

            stop5num = int(ipc.seencount*0.05)
            stop5sessions = 0
            for entry in ipc.counts()[-stop5num:]:
                stop5sessions += entry[0]
            print("Top 5%% of IPs (%s) account for %s sessions." % \
             (stop5num,stop5sessions))
            print("which is %0.2f%% of the total number of sessions." % \
             (stop5sessions/(sessions.seencount/100.0)))
            print() 

            print("Analyzed %s lines in %0.2f seconds, %0.2f lines per second" % \
             (linecount,rtime,linecount/rtime))
    except KeyboardInterrupt:
        sys.stderr.write("Interrupted. Probably your fault.\n")
        sys.exit(1)
    except ValueError:
        sys.stderr.write("Your logfile has a very strange format.\n")
        sys.exit(2)

if __name__ == "__main__":
    main()
