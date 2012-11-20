#!/usr/bin/python -tt

import unittest
import Sessions

class SessionsTest(unittest.TestCase):
    """Test Sessions class"""

    def setUp(self):
        self.sessions = [
            ("ses1", "foobaz"),
            ("ses2", "foobaz"),
            ("ses3", "foobar"),
            ("ses4", "creamcheese"),
            ]

    def testInit(self):
        myses = Sessions.Sessions()
        self.assertEqual(myses.accounts, {})
        self.assertEqual(myses.seencount, 0)
    
    def testPush(self):
        myses = Sessions.Sessions()
        self.assertEqual(myses.accounts, {})
        self.assertEqual(myses.seencount, 0)

        for (sessid, inf) in self.sessions:
            myses.push(sessid, inf)

        self.assertEqual(myses.seencount, len(self.sessions))


    def testPop(self):
        myses = Sessions.Sessions()
        self.assertEqual(myses.accounts, {})
        self.assertEqual(myses.seencount, 0)

        for (sessid, inf) in self.sessions:
            myses.push(sessid, inf)

        self.assertEqual(myses.seencount, len(self.sessions))
        for (sessid, inf) in self.sessions[::-1]:
            self.assertEqual(myses.pop(sessid), inf)

