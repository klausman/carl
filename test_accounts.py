#!/usr/bin/python -tt
"""Test suite for Accounts.py of Carl"""
import unittest
import Accounts

# Pylint has a counterproductive idea of proper names in this case. Also,
# docstrings for tests seem a bit overblown. TODO: find someone who cares
# enough to write them.
# pylint: disable=invalid-name,missing-docstring,too-many-public-methods,


class AccountsTest(unittest.TestCase):

    """Test Accounts class"""

    def setUp(self):
        self.keynames = ["mykey", "yourkey", "theirkey", "hiskey"]
        self.splitpoint = int(len(self.keynames) / 2)

    def testInit(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)

    def testIncr(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)

        for key in self.keynames:
            myac.incr(key)

        self.assertEqual(myac.seencount, len(self.keynames))
        for key in self.keynames:
            self.assertIn(key, myac.accounts.keys())
            self.assertEqual(myac.val(key), 1)

    def testDecr(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)

        for key in self.keynames:
            myac.decr(key)

        self.assertEqual(myac.seencount, len(self.keynames))
        for key in self.keynames:
            self.assertIn(key, myac.accounts.keys())
            self.assertEqual(myac.val(key), -1)

    def testUnseen(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)

        self.assertEqual(myac.val("randomschmandom"), 0)

    def testMultiIncr(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)

        for key in self.keynames:
            myac.incr(key)
        for key in self.keynames[self.splitpoint:]:
            myac.incr(key)

        for key in self.keynames[self.splitpoint:]:
            self.assertEqual(myac.val(key), 2)
        for key in self.keynames[:self.splitpoint]:
            self.assertEqual(myac.val(key), 1)

    def testIncrMore(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)
        for key in self.keynames:
            myac.incr(key, 42)
        self.assertEqual(myac.seencount, len(self.keynames))
        for key in self.keynames:
            self.assertIn(key, myac.accounts.keys())
            self.assertEqual(myac.val(key), 42)

    def testGetkeys(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)
        self.assertEqual(myac.counts(), [])
        self.assertEqual(myac.getkeys(), [])
        for key in self.keynames:
            myac.incr(key, 42)
        self.assertEqual(sorted(myac.getkeys()), sorted(self.keynames))

    def testCounts(self):
        myac = Accounts.Accounts()

        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)
        self.assertEqual(myac.counts(), [])
        for key in self.keynames:
            myac.incr(key, 42)
        self.assertEqual(myac.seencount, len(self.keynames))
        # since all the counts are the same now, we needn't care about order
        self.assertEqual(set(myac.counts()),
                         set([(42, x) for x in self.keynames]))
        myac = Accounts.Accounts()
        self.assertEqual(myac.accounts, {})
        self.assertEqual(myac.seencount, 0)
        self.assertEqual(myac.counts(), [])
        incr = 0
        for key in self.keynames:
            incr += 1
            myac.incr(key, incr)
        # Now we can assume order.
        self.assertEqual(myac.counts(),
                         [(1, 'mykey'), (2, 'yourkey'),
                          (3, 'theirkey'), (4, 'hiskey')])
        self.assertEqual(myac.counts(desc=True),
                         [(4, 'hiskey'), (3, 'theirkey'),
                          (2, 'yourkey'), (1, 'mykey')])


if __name__ == "__main__":
    unittest.main()
