"""Simple session tallying module"""

__revision__ = "1"

class Sessions:
    """Simple session tallying class"""
    
    def __init__(self):
        """Setup book keeping"""
        self.accounts = {}
        self.seencount = 0

    def push(self, sid, info):
        """Push session info into the list"""
        self.seencount += 1
        self.accounts[sid] = info

    def pop(self, sid):
        """Return the session for a session id"""
        return self.accounts.get(sid)
