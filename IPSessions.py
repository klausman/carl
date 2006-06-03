
class IPSessions:

    def __init__(self):
        self.T={}
        self.seencount=0

    def push(self,pid,ip):
        self.seencount+=1
        self.T[pid]=ip

    def pop(self,pid):
        return self.T.get(pid)
