'''
Simple interface into wowhead data.  Has some test stubs.
'''
import re

from google.appengine.api       import memcache
from macro.data.appengine.defs  import MEMCACHED_PARAM_INFO, MEMCACHED_PARAM_MISS

from macro.data.test.wow        import get_test_object
from macro.data.appengine.wow   import get_datastore_object
from macro.data.mmochampion.wow import get_mmochamp_object

# Available stores for wow data.
SOURCE_TEST         = 0
SOURCE_DATASTORE    = 1
SOURCE_MMOCHAMPION  = 2

# Constant for using memcache to prevent repeated lookups
# on misses.
MEMCACHED_NOT_FOUND = True

# Localization--here for future work.
DEFAULT_LANG        = "EN"


def get_wow_object(obj_id, is_id=False, is_item=False,
                   language=DEFAULT_LANG, src=SOURCE_DATASTORE,
                   cache={}, failover=False):
    ''' Interface into fetching wow object (item/spell) data.
    Uses memcachd and an optional local cache to keep down overhead. '''
    obj = None
    cachekey = _gen_cache_key(obj_id, is_item)

    # First check the cache
    if cache and cachekey in cache and cache[cachekey]:
        return cache[cachekey]

    # Next check memcache (non-test only)
    if src != SOURCE_TEST:
        obj = memcache.get(cachekey)
        if obj is not None:
            if obj == MEMCACHED_NOT_FOUND: return None
            return obj

    # Skip a lot of work if we're in test mode.
    if src == SOURCE_TEST:
        obj = get_test_object(obj_id, is_item)

    # if datastore is specified
    if src == SOURCE_DATASTORE:
        obj = get_datastore_object(obj_id, is_item)

    # if mmo-champion is specificied, or if fallback is allowed
    # and the datastore missed.
    if src == SOURCE_MMOCHAMPION or (not obj and failover):
        obj = get_mmochamp_object(obj_id, is_item)

    # Even on miss, update memcache to prevent repeat misses
    if src != SOURCE_TEST:
        # Update memcached
        if not obj:
            memcache.add(cachekey, MEMCACHED_NOT_FOUND, MEMCACHED_PARAM_MISS)
        else:
            memcache.add(cachekey, obj, MEMCACHED_PARAM_INFO)

    # Update local per-command cache before return
    cache[cachekey] = obj
    return obj


# Helper to noramalize lookups into cache keys
def _gen_cache_key(obj_id, is_item):
    obj_type = "i" if is_item else "s"
    cachekey = "%s%s" % (obj_type, obj_id.lower())
    return re.sub("\s+", " ", cachekey)

