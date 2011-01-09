#!/usr/bin/env python
try:
    import pydvice
    print "Loaded without looking"
except ImportError:
    import sys, os
    sys.path.append(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'lib'
    ))
    import pydvice
    print "Loaded by guessing where lib is"
except ImportError:
    print "Failed to load the library!"
    exit(0xff)
