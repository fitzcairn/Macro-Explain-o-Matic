'''
Gated counter using memcached for high concurrency without
sharding.

From:
http://appengine-cookbook.appspot.com/recipe/high-concurrency-counters-without-sharding

Modified from solutions suggested by Bill Katz and Nick Johnson
'''

import logging

from google.appengine.api import memcache
from google.appengine.api.capabilities import CapabilitySet
from google.appengine.ext import db

# Counter key prefixes
_MACRO_COUNT  = "_count"
_MACRO_LOCK   = "_lock"
_MACRO_INCR   = "_inc"

# How often (in seconds) we should update the counter in the
# underlying appstore entity.  This is just a default.
_DEF_UPDATE_INTERVAL = 30

# Logging enable
_DEBUG = False


# Construct keys.
def _get_key(type, name, entity_key):
    return "_".join([type, name, entity_key])


# Init a counter.
def init_count(entity_key, counter_name, interval=_DEF_UPDATE_INTERVAL):
    lock_key  = _get_key(_MACRO_LOCK,  counter_name, entity_key)
    count_key = _get_key(_MACRO_COUNT, counter_name, entity_key)
    incr_key  = _get_key(_MACRO_INCR,  counter_name, entity_key)
    memcache.set(count_key, 0)
    memcache.set(incr_key,  0)
    memcache.add(lock_key,  None, time=interval)
    

# Get a counter value
def get_count(entity_key, counter_name, entity_val=0):
    ''' Get the value of this counter from memcached.
    On fail, return the current count saved in the
    datastore, passed in as entity_val'''
    count_key = _get_key(_MACRO_COUNT, counter_name, entity_key)
    incr_key  = _get_key(_MACRO_INCR,  counter_name, entity_key)

    # Read memcached
    value = memcache.get(count_key)
    incr  = int(memcache.get(incr_key) or 0)

    # On fail, insert/return the value from the datastore.
    if value is None:
        value = entity_val + incr
        memcache.set(count_key, value)
        if _DEBUG: logging.debug("Inner:   => val: %s, incr: %s" % (value, incr))
        return int(value)
    if _DEBUG: logging.debug("Outer:   => val: %s, incr: %s" % (value, incr))
    return int(value + incr)


# Increment a counter, updating the backing entity
# if the timer on the last update expired.
def incr_count(entity_key, counter_name, txn_def, incr_amt=1, interval=_DEF_UPDATE_INTERVAL, entity_val=0):
    ''' Increment a counter.  Updates a backing
    entity with contents of memcached.

    Can handle increments only right now. Returns nothing.
    Raises exception on error.'''

    # Don't worry about decrements right now.
    if incr_amt < 0:
        return 0

    # Generate memcached keys.
    lock_key  = _get_key(_MACRO_LOCK,  counter_name, entity_key)
    count_key = _get_key(_MACRO_COUNT, counter_name, entity_key)
    incr_key  = _get_key(_MACRO_INCR,  counter_name, entity_key)
    if _DEBUG: logging.debug("keys: %s %s %s" % (lock_key, count_key, incr_key))

    # Check to see if memecached is up.
    look_ahead_time = 10 + interval
    memcache_ops    = CapabilitySet('memcache', methods=['add'])
    memcache_down   = not memcache_ops.will_remain_enabled_for(look_ahead_time)

    # If memcache is down or interval seconds has passed, update
    # the datastore.
    if memcache_down or memcache.add(lock_key, None, time=interval):
        # Update the datastore
        incr = int(memcache.get(incr_key) or 0) + incr_amt
        if _DEBUG: logging.debug("incr(%s): updating datastore with %d", counter_name, incr)
        memcache.set(incr_key, 0)
        try:
            stored_count = db.run_in_transaction(txn_def, entity_key, incr, counter_name)
        except:
            memcache.set(incr_key, incr)
            logging.error('Counter(%s): unable to update datastore counter.', counter_name)
            raise
        memcache.set(count_key, stored_count)
        return stored_count
    # Majority of the time, this branch is taken.
    else:
        incr = memcache.get(incr_key)
        if incr is None:
            # incr_key in memcache should be set.  If not, two possibilities:
            # 1) memcache has failed between last datastore update.
            # 2) this branch has executed before memcache set in update branch (unlikely)
            stored_count = db.run_in_transaction(txn_def, entity_key, incr_amt, counter_name)
            memcache.set(count_key, stored_count)
            memcache.set(incr_key, 0)
            logging.error('Counter(%s): possible memcache failure in update interval.',
                          counter_name)
            return stored_count
        # Memcache increment.
        else:
            memcache.incr(incr_key, delta=incr_amt)
            if _DEBUG: logging.debug("incr(%s): incrementing memcache with %d", counter_name, incr_amt)
            return get_count(entity_key, counter_name, entity_val)

