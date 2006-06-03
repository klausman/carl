import time

class Account:

    def __init__(self):
        self.T={}
        self.seencount=0L

    def incr(self,k,num=1):
        try:
            self.T[k]=self.T[k]+num
        except:
            self.T[k]=0L+num
            self.seencount+=1L

    def decr(self,k,num=1):
        try:
            self.T[k]=self.T[k]-num
        except:
            self.T[k]=0L+num
            self.seencount+=1L

    def val(self,k):
        try:
            retval=self.T[k]
        except:
            retval=0

        return retval

    def getkeys(self):
        return self.T.keys()

    def counts(self,desc=None):
        '''Returns list of keys, sorted by values.
        Feed a 1 if you want a descending sort.'''
        i = map(lambda t: list(t),self.T.items())
        map(lambda r: r.reverse(),i)
        i.sort()
        if desc:
            i.reverse()
        return i

class IPSessions:

    def __init__(self):
        self.T={}
        self.seencount=0

    def push(self,pid,ip):
        self.seencount+=1
        self.T[pid]=ip

    def pop(self,pid):
        return self.T.get(pid)
