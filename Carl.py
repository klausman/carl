#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2012  Tobias Klausmann
#
"""
An rsync logfile analyzer.

Intended to be used mainly by Gentoo Rsync Mirror admins
"""
import sys
import time
import hashlib # pylint: disable=import-error

from optparse import OptionParser
from random import random

import Accounts
import Sessions

__version__ = "0.9"

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
SALT = "%s" % (random())

try:
    # pylint: disable=import-error
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
    while number >= div:
        number /= div
        passes += 1
    return (number, passes)


def obfuscate(data, style):
    """
    Return an obfuscated version of the string in the style specified
    (one of fancy, simple or everything else (being no obfuscation)).
    """
    if data != "" and style == "fancy":
        # This branch doesn't care about v4 vs v6
        md5sum = hashlib.new("md5")
        data += SALT
        md5sum.update(data.encode("utf8"))
        dig = md5sum.hexdigest()
        result = "%s...%s" % (dig[:8], dig[-8:])
    elif data != "" and style == "simple":
        if ":" in data:  # IPv6
            if data != "::1":
                sep = ":"
            else:
                return data # keep v6's localhost shorthand intact
        else:  # IPv4 and hostnames
            sep = "."

        result = sep.join(data.split(sep)[:2])+"..."

    else: # No obfuscation
        result = data

    return result

def parse_cmdline(argv):
    """
    Parse commandline stored in argv
    """
    msgs = []
    errmsgs = []
    usage = ("usage: %prog [options] [filename]\n\n"
             "If filename is not specified, read from stdin")
    lic = "Licensed under the GPL v2 (see COPYING). No warranty whatsoever."
    parser = OptionParser(usage=usage, version="%%prog %s\n%s" % 
                          (__version__, lic))
    parser.add_option("-o", "--obfuscation", action="store", type="string",
                    dest="ostyle", default="none",
                    help="obfuscation style (simple, fancy, none) [%default]")
    parser.add_option("-r", "--reverse", action="store_true",
                   dest="reverse", help="set reverse (classic) display order")
    parser.add_option("-s", "--short", action="store_true", default=False,
                   dest="shortoutput", help="display only the two top-10 lists")
    (options, args) = parser.parse_args(argv)

    if not options.shortoutput:
        msgs.append("Carl (Carl Analyzes Rsync Logfiles) %s" % __version__)
        msgs.append("(C) Tobias Klausmann")
        if __psyco_enabled__:
            msgs.append("Psyco found and enabled.")

    if len(args) > 1:
        fnames = args[1:]
        msgs.append("Reading from %s"% ", ".join(fnames))
    else:
        fnames = []
        if not options.shortoutput:
            msgs.append("Reading from stdin")

    return (options, fnames, msgs, errmsgs)

def getfilecontent(fname):
    """
    Open fname readonly, read its data and return it. If there is an IOError
    when read()ing or open()ing, write an error message to stderr and return
    nothing.
    """
    data = ""
    try:
        inputfile = open(fname)
        data += inputfile.read()
    except IOerror as eobj: # pylint: disable=undefined-variable
        sys.stderr.write("Could not read '%s': %s\n" % (fname, eobj))
    return data


def mkreport(options, stats):
    """Generate report from stats dictionary, heeding options."""
    output = []
   
    if not options.shortoutput:
        shorttt, pfxn = crunch(stats["totaltraffic"])
        output.append("Total traffic: %.2f %sBytes" % 
                      (shorttt, __SIPREFIXES__[pfxn]))
        output.append("Total number of sessions: %s" % 
                      stats["sessions"].seencount)
        output.append("Total number of unique IPs: %s" % 
                      stats["ipb"].seencount)
        output.append("Log seems to span %0.2f days." % (stats["span"]))
        output.append("")

    output.append(" Top 10 Hosts by byte count")
    output.append("Rank bytes     ( Bytes )     IP-Address")
    output.append("-----------------------------------------")

    top10list = stats["ipb"].counts()[-10:]
    ranklist = list(range(1, 11))

    if not options.reverse:
        top10list.reverse()
        ranklist.reverse()
    for entry in top10list:
        sbytes, pfxn = crunch(entry[0])
        output.append("%2s %12s (%9.2f%s) %15s %s" % 
            (ranklist.pop(), entry[0], sbytes,
             __SIPREFIXES__[pfxn], obfuscate(entry[1], options.ostyle), 
             obfuscate(stats["ip2hname"].get(entry[1], ""), options.ostyle)))

    output.append("-----------------------------------------")
    if not options.shortoutput:
        savg, pfxn = crunch(stats["totaltraffic"]/stats["span"])
        output.append("Average traffic per day: %0.2f bytes (%0.2f%sB)" % 
            (stats["totaltraffic"]/stats["span"], savg, __SIPREFIXES__[pfxn]))

        ttop5num = int(stats["ipb"].seencount*0.05)
        ttop5traffic = 0
        for entry in stats["ipb"].counts()[-ttop5num:]:
            ttop5traffic += entry[0]

        stop, pfxn = crunch(ttop5traffic)
        output.append("Top 5%% of IPs (%s) account for %s bytes (%0.2f%sB) "
                      "of traffic," % 
                      (ttop5num,ttop5traffic,stop,__SIPREFIXES__[pfxn]))
        output.append("which is %0.2f%% of the total traffic." % 
                      (ttop5traffic/(stats["totaltraffic"]/100.0)))

    output.append("")

    output.append(" Top 10 Hosts by session count")
    output.append("Rank Sess.   per day    IP-Address")
    output.append("----------------------------------")

    top10list = stats["ipc"].counts()[-10:]
    ranklist = list(range(1, 11))

    if not options.reverse:
        top10list.reverse()
        ranklist.reverse()

    for entry in top10list:
        output.append("%2s %6s    %6.2f   %15s %s"  % 
                      (ranklist.pop(), entry[0], entry[0]/stats["span"], 
                       obfuscate(entry[1], options.ostyle), 
                       obfuscate(stats["ip2hname"].get(entry[1], ""), 
                                 options.ostyle)))

    output.append("----------------------------------")

    if not options.shortoutput:
        output.append("Average number of sessions per day: %0.2f" % 
                      (stats["sessions"].seencount/stats["span"]))

        stop5num = int(stats["ipc"].seencount*0.05)
        stop5sessions = 0

        for entry in stats["ipc"].counts()[-stop5num:]:
            stop5sessions += entry[0]

        output.append("Top 5%% of IPs (%s) account for %s sessions," % 
                      (stop5num,stop5sessions))
        output.append("which is %0.2f%% of the total number of sessions." % 
                      (stop5sessions/(stats["sessions"].seencount/100.0)))
        output.append("")

        output.append("Analyzed %s lines in %0.2f seconds, %0.2f lines "
                      "per second" % 
                      (stats["linecount"], stats["rtime"], 
                       stats["linecount"]/stats["rtime"]))

    return("\n".join(output))


def parsedata(inputdata):
    """Parse data in inputdata and return stats dictionary."""
    stats = {}
    stats["ipc"] = Accounts.Accounts()
    stats["ipb"] = Accounts.Accounts()
    stats["sessions"] = Sessions.Sessions()
    stats["ip2hname"] = {}

    stats["linecount"] = 0
    stats["totaltraffic"] = 0
    stats["rtime"] = time.time()
    line = ""

    try:
        for line in inputdata.split("\n"):
            if not line:
                continue
            stats["linecount"] += 1
            try:
                ldate, ltime = line.split(None, 2)[0:2]
            except ValueError:
                continue

            if stats["linecount"] == 1:
                # timefmt: 2004/02/23 23:11:27
                stats["start"] = time.mktime(
                    time.strptime("%s %s"%(ldate, ltime), "%Y/%m/%d %H:%M:%S"))

            pid, msg = line[20:].split(" ", 1)
            if msg.startswith("rsync error: "):
                continue
            if (msg.startswith("rsync on %s" % (__MODULE__) ) and 
                not msg.startswith("rsync on %s/metadata" % (__MODULE__)) and 
                not msg.startswith("rsync on %s//metadata" % (__MODULE__))):
                try:
                    hname, ipaddr = msg.split(" ", 6)[4:6]
                except ValueError:
                    continue
                ipaddr = ipaddr[1:-2] # remove ()
                # Do some hostname caching which can be used for
                # output later
                if hname != "UNKNOWN" and not stats["ip2hname"].get(ipaddr):
                    stats["ip2hname"][ipaddr] = hname
                stats["ipc"].incr(ipaddr)
                stats["sessions"].push(pid, '%s' % (ipaddr))

            elif msg.startswith("sent"):
                try:
                    values = msg.split(" ", 11)
                    wbytes = values[1]
                    rbytes = values[5]
                except ValueError:
                    continue
                ipaddr = stats["sessions"].pop(pid)
                stats["ipb"].incr(ipaddr, int(wbytes)+int(rbytes))
                stats["totaltraffic"] += int(rbytes)+int(wbytes)

        stats["span"] = (
            (time.mktime(time.strptime("%s %s" % (ldate, ltime), 
                                       "%Y/%m/%d %H:%M:%S")) -
             stats["start"])/(24*3600))
        stats["rtime"] = time.time()-stats["rtime"]
    except ValueError:
        sys.stderr.write("Your logfile has a very strange format.\n")
        sys.exit(2)

    return stats



def main():
    """
    Main program.
    """

    (options, fnames, msgs, errmsgs) = parse_cmdline(sys.argv)
    if msgs:
        print("\n".join(msgs))
    if errmsgs:
        sys.stderr.write("\n".join(errmsgs))

    sys.stdout.flush()

    inputdata = ""

    for fname in fnames:
        inputdata += getfilecontent(fname)
    if len(fnames) ==0:
        inputdata = sys.stdin.read()

    try:
        print(mkreport(options, parsedata(inputdata)))

    except KeyboardInterrupt:
        sys.stderr.write("Interrupted. Probably your fault.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
