#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2003-2012  Tobias Klausmann
#
"""
An rsync logfile analyzer.

Intended to be used mainly by Gentoo Rsync Mirror admins
"""
import argparse
import sys
import time
import hashlib  # pylint: disable=import-error
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
                return data  # keep v6's localhost shorthand intact
        else:  # IPv4 and hostnames
            sep = "."

        result = sep.join(data.split(sep)[:2]) + "..."

    else:  # No obfuscation
        result = data

    return result


def parse_cmdline(argv):
    """
    Parse commandline stored in argv
    """
    msgs = []
    errmsgs = []
    lic = "Licensed under the GPL v2 (see COPYING). No warranty whatsoever."
    parser = argparse.ArgumentParser(prog="Carl %s\n%s" % (__version__, lic))
    parser.add_argument("-o", "--obfuscation", dest="ostyle", default="none",
                        help="obfuscation style (simple, fancy, none)")
    parser.add_argument("-r", "--reverse", action="store_true", dest="reverse",
                        help="set reverse (classic) display order")
    parser.add_argument("-s", "--short", action="store_true", default=False,
                        dest="shortoutput",
                        help="display only the two top-10 lists")
    parser.add_argument("-v", "--version", action="store_true", default=False)
    parser.add_argument("filename", nargs="?", type=argparse.FileType('r'),
                        default=sys.stdin)
    args = parser.parse_args(argv)

    return (args, msgs, errmsgs)


def mkreport(args, stats):
    """Generate report from stats dictionary, heeding args."""
    output = []

    if not args.shortoutput:
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

    if not args.reverse:
        top10list.reverse()
        ranklist.reverse()
    for entry in top10list:
        sbytes, pfxn = crunch(entry[0])
        output.append("%2s %12s (%9.2f%s) %15s %s" %
                      (ranklist.pop(), entry[0], sbytes,
                       __SIPREFIXES__[pfxn], obfuscate(
                           entry[1], args.ostyle),
                       obfuscate(stats["ip2hname"].get(entry[1], ""),
                                 args.ostyle)))

    output.append("-----------------------------------------")
    if not args.shortoutput:
        savg, pfxn = crunch(stats["totaltraffic"] / stats["span"])
        output.append("Average traffic per day: %0.2f bytes (%0.2f%sB)" %
                      (stats["totaltraffic"] / stats["span"], savg,
                       __SIPREFIXES__[pfxn]))

        ttop5num = int(stats["ipb"].seencount * 0.05)
        ttop5traffic = 0
        for entry in stats["ipb"].counts()[-ttop5num:]:
            ttop5traffic += entry[0]

        stop, pfxn = crunch(ttop5traffic)
        output.append("Top 5%% of IPs (%s) account for %s bytes (%0.2f%sB) "
                      "of traffic," %
                      (ttop5num, ttop5traffic, stop, __SIPREFIXES__[pfxn]))
        output.append("which is %0.2f%% of the total traffic." %
                      (ttop5traffic / (stats["totaltraffic"] / 100.0)))

    output.append("")

    output.append(" Top 10 Hosts by session count")
    output.append("Rank Sess.   per day    IP-Address")
    output.append("----------------------------------")

    top10list = stats["ipc"].counts()[-10:]
    ranklist = list(range(1, 11))

    if not args.reverse:
        top10list.reverse()
        ranklist.reverse()

    for entry in top10list:
        output.append("%2s %6s    %6.2f   %15s %s" %
                      (ranklist.pop(), entry[0], entry[0] / stats["span"],
                       obfuscate(entry[1], args.ostyle),
                       obfuscate(stats["ip2hname"].get(entry[1], ""),
                                 args.ostyle)))

    output.append("----------------------------------")

    if not args.shortoutput:
        output.append("Average number of sessions per day: %0.2f" %
                      (stats["sessions"].seencount / stats["span"]))

        stop5num = int(stats["ipc"].seencount * 0.05)
        stop5sessions = 0

        for entry in stats["ipc"].counts()[-stop5num:]:
            stop5sessions += entry[0]

        output.append("Top 5%% of IPs (%s) account for %s sessions," %
                      (stop5num, stop5sessions))
        output.append("which is %0.2f%% of the total number of sessions." %
                      (stop5sessions / (stats["sessions"].seencount / 100.0)))
        output.append("")

        output.append("Analyzed %s lines in %0.2f seconds, %0.2f lines "
                      "per second" %
                      (stats["linecount"], stats["rtime"],
                       stats["linecount"] / stats["rtime"]))

    return "\n".join(output)


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
    ldate = None
    ltime = None

    try:
        for line in inputdata.splitlines():
            if not line:
                continue
            stats["linecount"] += 1
            try:
                ldate, ltime = line.split(None, 2)[0:2]
            except ValueError:
                continue

            if stats["linecount"] == 1:
                try:
                    # timefmt: 2004/02/23 23:11:27
                    stats["start"] = time.mktime(
                        time.strptime("%s %s" % (ldate, ltime),
                                      "%Y/%m/%d %H:%M:%S"))
                except ValueError:
                    stats["linecount"] = 0  # Make sure we try the next one
                    continue

            try:
                pid, msg = line[20:].split(None, 1)
            except ValueError:
                continue
            msg = msg.strip()
            if not msg or msg.startswith("rsync error: "):
                continue
            if (msg.startswith("rsync on %s" % (__MODULE__)) and
                    (" %s/metadata" % (__MODULE__) not in msg)):

                try:
                    hname, ipaddr = msg.split(None, 6)[4:6]
                except ValueError:
                    continue
                ipaddr = ipaddr[1:-2]  # remove ()
                # Do some hostname caching which can be used for
                # output later
                if hname != "UNKNOWN" and not stats["ip2hname"].get(ipaddr):
                    stats["ip2hname"][ipaddr] = hname
                stats["ipc"].incr(ipaddr)
                stats["sessions"].push(pid, '%s' % (ipaddr))

            elif msg.startswith("sent"):
                try:
                    values = msg.split(None, 11)
                    wbytes = values[1].replace(",", "")
                    rbytes = values[4].replace(",", "")
                except ValueError:
                    continue
                ipaddr = stats["sessions"].pop(pid)
                stats["ipb"].incr(ipaddr, int(wbytes) + int(rbytes))
                stats["totaltraffic"] += int(rbytes) + int(wbytes)

        stats["span"] = "unknown"
        if ldate and ltime:
            try:
                stats["span"] = (
                    (time.mktime(time.strptime("%s %s" % (ldate, ltime),
                                               "%Y/%m/%d %H:%M:%S")) -
                     stats["start"]) / (24 * 3600))
            except ValueError:
                pass

        stats["rtime"] = time.time() - stats["rtime"]
    except ValueError:
        sys.stderr.write("Your logfile has a strange format (line %i).\n" %
                         (stats["linecount"]))
        sys.stderr.write("Line seen:\n" + line + "\n")
        raise

    return stats


def main():
    """
    Main program.
    """

    (args, msgs, errmsgs) = parse_cmdline(sys.argv[1:])

    if args.version:
        sys.stderr.write("Carl (Carl Analyzes Rsync Logfiles) v%s\n" %
                         (__version__))
        sys.exit(0)

    if not args.shortoutput:
        msgs.append("Carl (Carl Analyzes Rsync Logfiles) %s" % __version__)
        msgs.append("(C) Tobias Klausmann")

    if msgs:
        print("\n".join(msgs))
    if errmsgs:
        sys.stderr.write("\n".join(errmsgs))

    sys.stdout.flush()

    inputdata = args.filename.read()

    try:
        print(mkreport(args, parsedata(inputdata)))

    except KeyboardInterrupt:
        sys.stderr.write("Interrupted. Probably your fault.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
