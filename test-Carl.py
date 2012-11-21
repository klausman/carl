#!/usr/bin/python -tt

import sys
import unittest
import Carl

class SessionsTest(unittest.TestCase):
    """Test Sessions class"""

    def setUp(self):
        self.savedsalt = Carl.SALT
        Carl.SALT="lemon curry"

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

    # TODO: IPv6
    def testObFancy(self):
        golden = [("eenie", "b7259125...fd872fa5"),
                  ("meenie", "9d9b3703...5ae754db"),
                  ("miney", "3751a98b...89aad47b"),
                  ("moe", "1b9fd716...9196f82f"),
                 ]
        for (inp, out) in golden:
            self.assertEqual(out, Carl.ob(inp, "fancy"))

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
            self.assertEqual(out, Carl.ob(inp, "simple"))

    def testObNone(self):
        golden = ["127.0.0.1",
                  "192.168.65.3",
                  "172.19.22.4",
                  "2001::a:b:c:d",
                  "2001:db8:a:b:c::",
                 ]
        for inp in golden:
            self.assertEqual(inp, Carl.ob(inp, ""))


    def testParseCmdline(self):
        argv = ["carl", "-o", "fancy", "-r", "-s"]
        (options, args, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertEqual(args, ["carl"])
        self.assertEqual(options.shortoutput, True)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertEqual(msgs, [])
        self.assertEqual(errmsgs, [])

    def testParseCmdlineVerbose(self):
        argv = ["carl", "-o", "fancy", "-r"]
        (options, args, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertEqual(args, ["carl"])
        self.assertEqual(options.shortoutput, False)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertNotEqual(msgs, [])
        self.assertEqual(errmsgs, [])

    def testParseCmdlineVerboseWithArgs(self):
        argv = ["carl", "-o", "fancy", "-r", "foo", "bar", "baz"]
        (options, args, fnames, msgs, errmsgs) = Carl.parse_cmdline(argv)
        self.assertGreater(len(args), 1)
        self.assertEqual(args, ["carl", "foo", "bar", "baz"])
        self.assertEqual(options.shortoutput, False)
        self.assertEqual(options.ostyle, "fancy")
        self.assertEqual(options.reverse, True)
        self.assertNotEqual(msgs, [])
        self.assertNotEqual(fnames, [])
        self.assertEqual(errmsgs, [])


