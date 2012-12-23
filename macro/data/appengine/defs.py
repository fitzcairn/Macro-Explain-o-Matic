'''
Collection of appengine-specific constants.
'''

import os

_ver = os.environ["CURRENT_VERSION_ID"] 

''' Datastore key defs. '''
# Use the
DATA_KEY       = _ver + "%s"
MACRO_PROC_KEY = "_p" + _ver + "%s" # % macro_id
MACRO_VIEW_KEY = "view_%s" # % macro_id

''' Memcached Times '''

# Amount of time forced between sequential saves for a given user.
MEMCACHED_THROTTLE_SECONDS = 10

# Saving the entire processed macro is expensive space-wise, but saves
# us a LOT of time.  Therefore we give it a fairly short TTL.
MEMCACHED_MACRO_PROC  = 920

# The saved param information from the database.  Also a long TTL (12hrs),
# as this doesn't change often and is expensive to fetch.
MEMCACHED_PARAM_INFO = 259200

# Misses we'll cache for 1min before trying again.
MEMCACHED_PARAM_MISS = 60

# Time for storing the static parts view pages in memcached--5min
MEMCACHED_VIEWS = 300

# Time for storing static tooltips in memcached--1min
MEMCACHED_TT = 60

# Time for storing api lookups in memcached--2min
MEMCACHED_API = 120


# Null entry for memcache.
NOP = False
