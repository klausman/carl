"""
Simple Accounting module
"""

__revision__ = "1"

class Accounts:
    """
    Simple Accounting class
    """

    def __init__(self):
        """Initialize book keeping"""
        self.accounts = {}
        self.seencount = 0

    def incr(self, k, num = 1):
        """Increment 'k' by 'num'"""
        try:
            self.accounts[k] = self.accounts[k]+num
        except KeyError:
            self.accounts[k] = 0+num
            self.seencount += 1

    def decr(self, k, num = 1):
        """Decrement 'k' by 'num'"""
        try:
            self.accounts[k] = self.accounts[k]-num
        except KeyError:
            self.accounts[k] = 0+num
            self.seencount += 1

    def val(self, k):
        """Return value of 'k'"""
        try:
            retval = self.accounts[k]
        except KeyError:
            retval = 0

        return retval

    def getkeys(self):
        """Return all keys"""
        return list(self.accounts.keys())

    def counts(self, desc=None):
        '''Returns list of keys, sorted by values.
        Feed a 1 if you want a descending sort.'''
        i = [[value, key] for key, value in list(self.accounts.items())]
        i.sort()
        if desc:
            i.reverse()
        return i
