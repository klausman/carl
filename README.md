# Carl - Carl Analyzes RSync Logfiles

This is Carl. Carl analyzes rsync logfiles and creates a top ten
list of users (or rather: IPs) both regarding volume and number of
sessions. 

Carl can be installed using the distutils method (`python setup.py install`)
or it can be run from its directory. Since Carl does not care what the form of
the IP addresses in the logfile is, it is agnostic regarding IPv4/6
addresses, except for simple anonymization. In that mode, it will shorten v4
addresses to two octets (e.g. `198.51.`) and v6 addresses to the second
colon (i.e. `2001::` or `2001:db8:`)

Note that from version 0.9 onward, Carl supports Python 3 while still being
compatible with Python version 2.6 and later.

There is a test suite (`test-*.py`), It can be run directly (`python
test-xyz.py`) or through Nose (just run `nosetests` in the topmost source
directory).

The newest version is available here:
http://www.schwarzvogel.de/software/misc.html

I can be reached at klausman-carl@schwarzvogel.de

Have fun.
