#!/usr/bin/python -tt
"""Test suite for Carl.py from Carl"""
import mock
import unittest
import Accounts
import Sessions
import Carl

# Pylint has a counterproductive idea of proper names in this case. Also,
# docstrings for tests seem a bit overblown. TODO: find someone who cares
# enough to write them.
# pylint: disable=invalid-name,missing-docstring,too-many-public-methods


class CarlHelpersTest(unittest.TestCase):

    """Test Sessions class"""

    def setUp(self):
        self.savedsalt = Carl.SALT
        Carl.SALT = "lemon curry"

        class mocked_fileobj:
            # pylint: disable=too-few-public-methods

            def __init__(self, readfunc=None):
                if not readfunc:
                    self.read = mock.MagicMock(
                        return_value="contents shmontents")
                else:
                    self.read = readfunc
        self.mocked_fileobj = mocked_fileobj

    def tearDown(self):
        Carl.SALT = self.savedsalt

    def testCrunchDefDiv(self):
        golden = [(1, (1, 0)),
                  (512, (512, 0)),
                  (1024, (1, 1)),
                  (1025, (1.0009765625, 1)),
                  (4096, (4, 1)),
                  (8192, (8, 1)),
                  (10240, (10, 1)),
                  (894352, (873.390625, 1)),
                  (3465298345823, (3.1516704855, 4)),
                  ]
        for (inp, out) in golden:
            (res, mag) = Carl.crunch(inp)
            self.assertAlmostEqual(res, out[0])
            self.assertEqual(mag, out[1])

    def testCrunchSIDev(self):
        golden = [(1, (1, 0)),
                  (1000, (1, 1)),
                  (1001, (1.001, 1)),
                  (4000, (4, 1)),
                  (8000, (8, 1)),
                  (10000, (10, 1)),
                  (894352, (894.352, 1)),
                  (3465298345823, (3.465298345823, 4)),
                  ]
        for (inp, out) in golden:
            (res, mag) = Carl.crunch(inp, 1000)
            self.assertAlmostEqual(res, out[0])
            self.assertEqual(mag, out[1])

    def testObFancy(self):
        golden = [("eenie", "b7259125...fd872fa5"),
                  ("meenie", "9d9b3703...5ae754db"),
                  ("miney", "3751a98b...89aad47b"),
                  ("moe", "1b9fd716...9196f82f"),
                  ]
        for (inp, out) in golden:
            self.assertEqual(out, Carl.obfuscate(inp, "fancy"))

    def testObSimple(self):
        golden = [("127.0.0.1", "127.0..."),
                  ("192.168.65.3", "192.168..."),
                  ("172.19.22.4", "172.19..."),
                  ("10.4.2.65", "10.4..."),
                  ("2001::a:b:c:d", "2001:..."),
                  ("2001:db8:a:b:c::", "2001:db8..."),
                  ("::1", "::1"),
                  ]
        for (inp, out) in golden:
            self.assertEqual(out, Carl.obfuscate(inp, "simple"))

    def testObNone(self):
        golden = ["127.0.0.1",
                  "192.168.65.3",
                  "172.19.22.4",
                  "2001::a:b:c:d",
                  "2001:db8:a:b:c::",
                  ]
        for inp in golden:
            self.assertEqual(inp, Carl.obfuscate(inp, ""))

    def testParseCmdline(self):
        argv = ["carl", "-o", "fancy", "-r", "-s"]
        (options, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertEqual(options.shortoutput, True)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertEqual(fnames, [])
        self.assertEqual(msgs, [])
        self.assertEqual(errmsgs, [])

    def testParseCmdlineVerbose(self):
        argv = ["carl", "-o", "fancy", "-r"]
        (options, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertEqual(fnames, [])
        self.assertEqual(options.shortoutput, False)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertNotEqual(msgs, [])
        self.assertEqual(errmsgs, [])

    def testParseCmdlineVerboseWithArgs(self):
        argv = ["carl", "-o", "fancy", "-r", "foo", "bar", "baz"]
        (options, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertEqual(fnames, ["foo", "bar", "baz"])
        self.assertEqual(options.shortoutput, False)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertNotEqual(msgs, [])
        self.assertNotEqual(fnames, [])
        self.assertEqual(errmsgs, [])

    def testGetfilecontent(self):
        myobj = self.mocked_fileobj()

        mocked_open = mock.MagicMock(return_value=myobj)

        Carl.open = mocked_open
        ret = Carl.getfilecontent("somefile")
        mocked_open.assert_called_with("somefile")
        myobj.read.assert_called_with()
        self.assertEqual(ret, "contents shmontents")
        del Carl.open

    def testGetfilecontentWithIOError(self):
        mocked_sys_stderr = mock.MagicMock()
        mocked_sys_stderr.write = mock.MagicMock()
        myobj = self.mocked_fileobj()
        mocked_open = mock.MagicMock(return_value=myobj, side_effect=IOError)
        Carl.open = mocked_open
        saved_stderr = Carl.sys.stderr
        Carl.sys.stderr = mocked_sys_stderr

        ret = Carl.getfilecontent("somefile")
        mocked_open.assert_called_with("somefile")
        self.assertTrue(Carl.sys.stderr.write.called)
        self.assertEqual(ret, "")
        del Carl.open
        Carl.sys.stderr = saved_stderr


class ReportTests(unittest.TestCase):

    def setUp(self):
        gigabyte = 1024 ** 3
        self.stats = {}
        self.stats["ip2hname"] = {"127.0.0.1": "localhost.example.com",
                                  "192.168.65.3": "rfc1918-1.example.com",
                                  "172.19.22.4": "rfc1918-2.example.com",
                                  "10.4.2.65": "rfc1918-3.example.com",
                                  "2001::a:b:c:d": "ipv6-1.example.com",
                                  "2001:db8:a:b:c::": "ipv6-2.example.com"}
        self.stats["linecount"] = 10 ** 9
        self.stats["rtime"] = 1
        self.stats["span"] = 86400
        self.stats["start"] = 0
        self.stats["totaltraffic"] = 72 * gigabyte
        self.stats["ipb"] = Accounts.Accounts()
        self.stats["ipc"] = Accounts.Accounts()
        for ip in self.stats["ip2hname"].keys():
            self.stats["ipb"].incr(ip, 1024 * 2 ** 5)
            self.stats["ipc"].incr(ip, 10)
        self.stats["sessions"] = Sessions.Sessions()
        self.stats["sessions"].seencount = 1000

    def testMkReport(self):
        argv = ["carl"]
        options = Carl.parse_cmdline(argv)[0]
        ret = Carl.mkreport(options, self.stats)
        for (key, value) in self.stats["ip2hname"].items():
            self.assertIn(key, ret)
            self.assertIn(value, ret)

        self.assertIn("Total traffic: 72.00 GBytes", ret)
        self.assertIn("Total number of sessions: 1000", ret)
        self.assertIn("Total number of unique IPs: %i" %
                      len(self.stats["ip2hname"]), ret)
        self.assertIn("Log seems to span 86400.00 days.", ret)
        self.assertIn("account for 60 sessions", ret)
        self.assertIn("1000000000 lines in 1.00 seconds, "
                      "1000000000.00 lines per second", ret)

    def testMkReportObfuscFancy(self):
        argv = ["carl", "-o", "fancy"]
        options = Carl.parse_cmdline(argv)[0]
        ret = Carl.mkreport(options, self.stats)
        for (key, value) in self.stats["ip2hname"].items():
            self.assertNotIn(key, ret)
            self.assertNotIn(value, ret)

    def testMkReportObfuscSimple(self):
        argv = ["carl", "-o", "simple"]
        options = Carl.parse_cmdline(argv)[0]
        ret = Carl.mkreport(options, self.stats)
        for (key, value) in self.stats["ip2hname"].items():
            self.assertNotIn(key, ret)
            self.assertNotIn(value, ret)


def testGarbage():
    mocked_sys_exit = mock.MagicMock()
    mocked_sys_stderr = mock.MagicMock()
    mocked_sys_stderr.write = mock.MagicMock()
    saved_sys_exit = Carl.sys.exit
    saved_stderr = Carl.sys.stderr
    Carl.sys.stderr = mocked_sys_stderr
    Carl.sys.exit = mocked_sys_exit
    Carl.parsedata("I have no log and I must scream.")
    mocked_sys_exit.assert_called_with(2)
    Carl.sys.exit = saved_sys_exit
    # We don't really care about _what_ was written. Or anything at all.
    Carl.sys.stderr = saved_stderr


def testNoLines():
    Carl.parsedata("")


def testGarbageMulti():
    Carl.parsedata("Demogorgon")


def testSession():
    inp = open("testdata/test_snippet1.log").read()
    Carl.parsedata(inp)

def testNumbersWithCommas():
    inp = open("testdata/test_commas_in_numbers.log").read()
    Carl.parsedata(inp)
